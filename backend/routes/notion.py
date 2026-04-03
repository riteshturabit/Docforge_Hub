import os
import time
from fastapi import APIRouter, HTTPException
from notion_client import Client
from dotenv import load_dotenv
from backend.database import get_connection

load_dotenv()

router = APIRouter()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DB_ID  = os.getenv("NOTION_DB_ID")


def chunk_blocks(blocks, size=100):
    for i in range(0, len(blocks), size):
        yield blocks[i:i + size]


def notion_create_with_retry(notion, **kwargs):
    for attempt in range(3):
        try:
            return notion.pages.create(**kwargs)
        except Exception as e:
            if "rate_limited" in str(e).lower() or "429" in str(e):
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise e
    raise HTTPException(status_code=429, detail="Notion rate limit exceeded")


def notion_append_with_retry(notion, block_id, children):
    for attempt in range(3):
        try:
            return notion.blocks.children.append(
                block_id=block_id,
                children=children
            )
        except Exception as e:
            if "rate_limited" in str(e).lower() or "429" in str(e):
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise e
    raise HTTPException(status_code=429, detail="Notion rate limit exceeded")


@router.post("/push_to_notion")
def push_to_notion(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT d.title, d.created_at, d.version,
               dt.industry, dty.name, dep.name
        FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        JOIN document_types dty ON dt.document_type_id = dty.id
        JOIN departments dep ON dt.department_id = dep.id
        WHERE d.id = %s
        """,
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    title      = result[0]
    created_at = result[1]
    version    = result[2] or "v1.0"
    industry   = result[3] or "SaaS"
    doc_type   = result[4]
    department = result[5]
    created_by = "DocForge"

    cursor.execute(
        """
        SELECT section_title, section_content
        FROM document_sections
        WHERE document_id=%s AND is_latest=TRUE
        ORDER BY section_order
        """,
        (document_id,)
    )
    sections = cursor.fetchall()
    if not sections:
        raise HTTPException(status_code=400, detail="No sections to publish")

    children = []
    for sec_title, sec_content in sections:
        children.append({
            "object": "block",
            "type":   "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": sec_title}}]
            }
        })
        if sec_content:
            for line in sec_content.split("\n"):
                line = line.strip()
                if line:
                    children.append({
                        "object": "block",
                        "type":   "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line[:1990]}}]
                        }
                    })

    response = notion_create_with_retry(
        notion,
        parent={"database_id": DB_ID},
        properties={
            "Name":        {"title":       [{"type": "text", "text": {"content": str(title)}}]},
            "Type":        {"select":      {"name": str(doc_type)}},
            "Industry":    {"select":      {"name": str(industry)}},
            "Version":     {"rich_text":   [{"type": "text", "text": {"content": str(version)}}]},
            "Tags":        {"multi_select": [{"name": str(department)}]},
            "Created_By":  {"rich_text":   [{"type": "text", "text": {"content": created_by}}]},
            "Created_at":  {"date":        {"start": str(created_at)}}
        }
    )

    page_id = response["id"]

    for block_chunk in chunk_blocks(children):
        notion_append_with_retry(notion, block_id=page_id, children=block_chunk)
        time.sleep(0.3)

    cursor.execute(
        "UPDATE documents SET notion_page_id=%s WHERE id=%s",
        (page_id, document_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "message":        "Published to Notion",
        "notion_page_id": page_id,
        "title":          title,
        "type":           doc_type,
        "industry":       industry,
        "version":        version,
        "department":     department,
        "template_id":    document_id
    }