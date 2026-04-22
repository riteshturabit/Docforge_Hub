import os
import json
import logging
from fastapi import APIRouter, HTTPException
from notion_client import Client
from dotenv import load_dotenv
from statecase.backend.models.ticket_models import (
    TicketRequest,
    TicketResponse
)
from statecase.backend.redis_client import set_ticket_lock
from statecase.backend.database import get_connection, release_connection

load_dotenv()
router = APIRouter()
logger = logging.getLogger("statecase.tickets")

notion        = Client(auth=os.getenv("NOTION_TOKEN"))
TICKETS_DB_ID = os.getenv("NOTION_TICKETS_DB_ID")


@router.post("/tickets", response_model=TicketResponse)
def create_ticket(data: TicketRequest):
    """
    Create support ticket in Notion.

    Flow:
    1. Check Redis lock → prevent duplicates
    2. Create Notion page with full context
    3. Save to PostgreSQL for tracking
    4. Return ticket ID + URL
    """

    # Duplicate prevention
    if not set_ticket_lock(data.question):
        logger.warning(
            f"Duplicate ticket prevented | "
            f"session={data.session_id}"
        )
        raise HTTPException(
            status_code=409,
            detail="Ticket already created for this question recently."
        )

    try:
        # Create Notion page
        notion_page = notion.pages.create(
            parent={"database_id": TICKETS_DB_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": data.question[:100]}}]
                },
                "Status": {
                    "select": {"name": "Open"}
                },
                "Priority": {
                    "select": {"name": data.priority}
                },
                "Session ID": {
                    "rich_text": [{"text": {"content": data.session_id}}]
                },
                "Assigned Owner": {
                    "rich_text": [{"text": {"content": data.assigned_owner}}]
                },
            },
            children=[
                {
                    "object": "block",
                    "type":   "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Question"}}]
                    }
                },
                {
                    "object": "block",
                    "type":   "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": data.question}}]
                    }
                },
                {
                    "object": "block",
                    "type":   "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Sources Attempted"}}]
                    }
                },
                {
                    "object": "block",
                    "type":   "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": (
                            ", ".join(data.sources_tried)
                            if data.sources_tried
                            else "No matching sources found"
                        )}}]
                    }
                },
                {
                    "object": "block",
                    "type":   "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Summary"}}]
                    }
                },
                {
                    "object": "block",
                    "type":   "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": data.summary}}]
                    }
                },
            ]
        )

        notion_ticket_id = notion_page["id"]
        notion_url = (
            f"https://notion.so/"
            f"{notion_ticket_id.replace('-', '')}"
        )

        # Save to PostgreSQL
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO sc_tickets
                (session_id, notion_ticket_id, question,
                 attempted_sources, summary, priority,
                 status, assigned_owner)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    data.session_id,
                    notion_ticket_id,
                    data.question,
                    json.dumps(data.sources_tried),
                    data.summary,
                    data.priority,
                    "Open",
                    data.assigned_owner
                )
            )
            conn.commit()
        finally:
            cursor.close()
            release_connection(conn)

        logger.info(
            f"Ticket created | "
            f"notion_id={notion_ticket_id} | "
            f"priority={data.priority}"
        )

        return TicketResponse(
            status="created",
            notion_ticket_id=notion_ticket_id,
            notion_url=notion_url,
            priority=data.priority
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket creation failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets")
def get_tickets(session_id: str = None):
    """Get all tickets or filter by session"""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        if session_id:
            cursor.execute(
                """
                SELECT id, notion_ticket_id, question,
                       priority, status, assigned_owner,
                       created_at
                FROM sc_tickets
                WHERE session_id=%s
                ORDER BY created_at DESC
                """,
                (session_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, notion_ticket_id, question,
                       priority, status, assigned_owner,
                       created_at
                FROM sc_tickets
                ORDER BY created_at DESC
                LIMIT 50
                """
            )

        rows = cursor.fetchall()
        return [
            {
                "id":               r[0],
                "notion_ticket_id": r[1],
                "question":         r[2],
                "priority":         r[3],
                "status":           r[4],
                "assigned_owner":   r[5],
                "created_at":       str(r[6]),
                "notion_url": (
                    f"https://notion.so/{r[1].replace('-','')}"
                    if r[1] else None
                )
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)