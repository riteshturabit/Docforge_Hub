from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    message:    str
    industry:   Optional[str] = None


class StateResponse(BaseModel):
    session_id:              str
    reply:                   str
    state:                   str
    citations:               list   = []
    ticket_id:               Optional[str] = None
    needs_clarification:     bool   = False
    clarification_question:  Optional[str] = None
    confidence:              float  = 0.0