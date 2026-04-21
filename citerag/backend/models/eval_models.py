from pydantic import BaseModel
from typing import Optional


class EvalRequest(BaseModel):
    run_name:  str
    questions: list[str]
    filters:   Optional[dict] = None


class EvalResult(BaseModel):
    question:     str
    answer:       str
    citations:    list[dict]
    confidence:   float
    has_evidence: bool
    chunks_used:  int


class EvalResponse(BaseModel):
    run_name:        str
    total_questions: int
    answered:        int
    answer_rate:     float
    avg_confidence:  float
    faithfulness:    float
    answer_relevancy:float
    results:         list[EvalResult]