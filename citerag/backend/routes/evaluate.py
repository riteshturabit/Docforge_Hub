import json
import logging
from fastapi import APIRouter, HTTPException
from citerag.backend.models.eval_models import (
    EvalRequest,
    EvalResponse,
    EvalResult
)
from citerag.backend.models.answer_models import AnswerRequest
from citerag.backend.routes.answer import answer_question
from citerag.backend.database import get_connection, release_connection

router = APIRouter()
logger = logging.getLogger("citerag.routes.evaluate")


@router.post("/evaluate")
def run_evaluation(data: EvalRequest):
    """
    Run evaluation batch on list of questions.

    For each question:
    1. Call answer endpoint
    2. Record: answer, citations, confidence, has_evidence
    3. Calculate aggregate scores
    4. Save run to PostgreSQL

    Metrics:
    → answer_rate     = % questions answered
    → avg_confidence  = average confidence score
    → faithfulness    = confidence / 100 (proxy)
    → answer_relevancy = answer_rate / 100 (proxy)
    """
    logger.info(
        f"Eval run started | "
        f"run={data.run_name} | "
        f"questions={len(data.questions)}"
    )

    results = []

    for question in data.questions:
        try:
            ans_req = AnswerRequest(
                query=question,
                session_id=f"eval_{data.run_name}",
                filters=data.filters
            )
            result = answer_question(ans_req)

            results.append(EvalResult(
                question=question,
                answer=result["answer"],
                citations=result["citations"],
                confidence=result["confidence"],
                has_evidence=result["has_evidence"],
                chunks_used=len(result["chunks"])
            ))
        except Exception as e:
            logger.error(f"Eval question failed | {e}")
            results.append(EvalResult(
                question=question,
                answer="Error during evaluation",
                citations=[],
                confidence=0.0,
                has_evidence=False,
                chunks_used=0
            ))

    # Calculate aggregate metrics
    answered       = [r for r in results if r.has_evidence]
    avg_confidence = (
        sum(r.confidence for r in answered) / len(answered)
        if answered else 0.0
    )
    answer_rate = (
        len(answered) / len(results) * 100
        if results else 0.0
    )

    # Save to PostgreSQL
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO citerag_eval_runs
            (run_name, config, dataset, results,
             faithfulness, answer_relevancy, context_precision)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data.run_name,
                json.dumps({"filters": data.filters}),
                json.dumps(data.questions),
                json.dumps([r.dict() for r in results]),
                round(avg_confidence / 100, 3),
                round(answer_rate / 100, 3),
                round(avg_confidence / 100, 3)
            )
        )
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)

    logger.info(
        f"Eval complete | "
        f"run={data.run_name} | "
        f"answered={len(answered)}/{len(results)}"
    )

    return EvalResponse(
        run_name=data.run_name,
        total_questions=len(results),
        answered=len(answered),
        answer_rate=round(answer_rate, 1),
        avg_confidence=round(avg_confidence, 1),
        faithfulness=round(avg_confidence / 100, 3),
        answer_relevancy=round(answer_rate / 100, 3),
        results=results
    )


@router.get("/evaluate/history")
def get_eval_history():
    """Get all past evaluation runs"""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, run_name, faithfulness,
                   answer_relevancy, context_precision,
                   created_at
            FROM citerag_eval_runs
            ORDER BY created_at DESC
            LIMIT 20
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id":                r[0],
                "run_name":          r[1],
                "faithfulness":      r[2],
                "answer_relevancy":  r[3],
                "context_precision": r[4],
                "created_at":        str(r[5])
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)