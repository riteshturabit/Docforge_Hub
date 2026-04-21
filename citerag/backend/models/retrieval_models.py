from pydantic import BaseModel
from typing import Optional


class RetrievalRequest(BaseModel):
    query:   str
    top_k:   int            = 5
    filters: Optional[dict] = None


class ChunkResult(BaseModel):
    qdrant_id:      str
    score:          float
    confidence:     float
    doc_title:      str
    section_title:  str
    chunk_text:     str
    notion_page_id: str
    industry:       Optional[str] = None
    doc_type:       Optional[str] = None
    version:        Optional[str] = None
    chunk_index:    int


class RetrievalResponse(BaseModel):
    query:     str
    chunks:    list[ChunkResult]
    citations: list[dict]
    total:     int