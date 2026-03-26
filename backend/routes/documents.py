import uuid
from fastapi import APIRouter, HTTPException
from backend.database import get_connection

router = APIRouter()


@router.post("/create-document")
def create_document(template_id: int, company_id: int):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM document_templates WHERE id=%s",
        (template_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")

    template_name = result[0]
    document_id   = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT INTO documents (id, template_id, company_id, title)
        VALUES (%s, %s, %s, %s)
        """,
        (document_id, template_id, company_id, template_name)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"document_id": document_id, "title": template_name}


@router.get("/documents")
def get_all_documents(department_id: int = None):
    conn   = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            d.id, d.title, d.version, d.status,
            d.created_at, d.notion_page_id,
            dt.name AS template_name, dt.industry,
            dep.name AS department_name,
            dty.name AS document_type,
            cc.company_name,
            d.quality_score
        FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        JOIN departments dep ON dt.department_id = dep.id
        JOIN document_types dty ON dt.document_type_id = dty.id
        LEFT JOIN company_context cc ON d.company_id = cc.id
        {where}
        ORDER BY d.created_at DESC
    """

    if department_id:
        cursor.execute(
            query.format(where="WHERE dep.id = %s"),
            (department_id,)
        )
    else:
        cursor.execute(query.format(where=""))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    documents = []
    for row in rows:
        documents.append({
            "id":             row[0],
            "title":          row[1],
            "version":        row[2],
            "status":         row[3],
            "created_at":     str(row[4]),
            "notion_page_id": row[5],
            "is_published":   row[5] is not None,
            "template_name":  row[6],
            "industry":       row[7],
            "department":     row[8],
            "document_type":  row[9],
            "company_name":   row[10],
            "quality_score":  row[11]
        })

    return {"total": len(documents), "documents": documents}


@router.get("/document/{document_id}")
def get_document(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            dt.name, d.version, d.status, d.created_at,
            d.notion_page_id, dep.name, dty.name, cc.company_name,
            d.quality_score
        FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        JOIN departments dep ON dt.department_id = dep.id
        JOIN document_types dty ON dt.document_type_id = dty.id
        LEFT JOIN company_context cc ON d.company_id = cc.id
        WHERE d.id = %s
        """,
        (document_id,)
    )
    meta = cursor.fetchone()
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    cursor.execute(
        """
        SELECT DISTINCT ON (section_order)
            section_title, section_content, section_order
        FROM document_sections
        WHERE document_id=%s
        ORDER BY section_order, id DESC
        """,
        (document_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "id":             document_id,
        "title":          meta[0],
        "version":        meta[1],
        "status":         meta[2],
        "created_at":     str(meta[3]),
        "is_published":   meta[4] is not None,
        "notion_page_id": meta[4],
        "department":     meta[5],
        "document_type":  meta[6],
        "company_name":   meta[7],
        "quality_score":  meta[8],
        "sections": [
            {"title": r[0], "content": r[1], "order": r[2]}
            for r in rows
        ]
    }


@router.get("/progress/{document_id}")
def get_progress(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT template_id FROM documents WHERE id=%s",
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    template_id = result[0]

    cursor.execute(
        "SELECT COUNT(*) FROM template_sections WHERE template_id=%s",
        (template_id,)
    )
    total_sections = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM document_sections
        WHERE document_id=%s AND is_completed=TRUE
        """,
        (document_id,)
    )
    completed_sections = cursor.fetchone()[0]

    progress = 0
    if total_sections > 0:
        progress = (completed_sections / total_sections) * 100

    cursor.close()
    conn.close()

    return {
        "completed_sections": completed_sections,
        "total_sections":     total_sections,
        "progress":           round(progress, 2)
    }