from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    database_id:    str
    force_reingest: bool = False


class IngestResponse(BaseModel):
    status:          str
    pages_ingested:  int
    total_chunks:    int
    message:         str