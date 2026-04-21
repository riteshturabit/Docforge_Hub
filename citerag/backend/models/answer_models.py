from pydantic import BaseModel
from typing import Optional


class AnswerRequest(BaseModel):
    query:      str
    session_id: str
    top_k:      int            = 5
    filters:    Optional[dict] = None


class AnswerResponse(BaseModel):
    question:     str
    answer:       str
    citations:    list[dict]
    chunks:       list[dict]
    has_evidence: bool
    confidence:   float
    session_id:   str