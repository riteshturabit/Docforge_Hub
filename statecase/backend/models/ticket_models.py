from pydantic import BaseModel
from typing import Optional


class TicketRequest(BaseModel):
    session_id:      str
    question:        str
    sources_tried:   list  = []
    summary:         str
    priority:        str   = "Medium"
    assigned_owner:  str   = "Support Team"


class TicketResponse(BaseModel):
    status:           str
    notion_ticket_id: str
    notion_url:       str
    priority:         str