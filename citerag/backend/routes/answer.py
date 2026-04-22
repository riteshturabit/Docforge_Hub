import json
import logging
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from citerag.backend.models.answer_models import (
    AnswerRequest,
    AnswerResponse
)
from citerag.backend.llm import llm
from citerag.backend.rag.retriever import (
    retrieve_chunks,
    check_evidence_strength
)
from citerag.backend.rag.citations import (
    build_citations,
    format_citations_for_prompt,
    get_avg_confidence
)
from citerag.backend.prompts.answer_prompt import ANSWER_PROMPT
from citerag.backend.utils.text_utils import build_context_string
from citerag.backend.redis_client import (
    cache_session,
    get_session,
    check_rate_limit
)
from citerag.backend.database import get_connection, release_connection
from citerag.backend.constants import (
    CACHE_TTL_SESSION,
    RATE_LIMIT_ANSWER,
    RATE_LIMIT_WINDOW,
    MEMORY_MESSAGES
)

router = APIRouter()
logger = logging.getLogger("citerag.routes.answer")

# No answer message
NO_ANSWER = (
    "I don't have sufficient information in the "
    "current document library to answer this "
    "question confidently."
)


@router.post("/answer")
def answer_question(data: AnswerRequest):
    """
    Generate grounded answer with citations.

    Flow:
    1. Rate limit check
    2. Retrieve relevant chunks from Qdrant
    3. Check evidence strength (anti-hallucination)
    4. If weak evidence → return NO_ANSWER
    5. Build context + get session history
    6. Generate answer via LLM
    7. Save to PostgreSQL + update Redis session
    8. Return answer + citations + confidence
    """

    # Rate limiting
    if not check_rate_limit(
        f"answer_{data.session_id}",
        max_calls=RATE_LIMIT_ANSWER,
        window=RATE_LIMIT_WINDOW
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait."
        )

    try:
        # Retrieve chunks
        chunks = retrieve_chunks(
            data.query,
            data.top_k,
            data.filters
        )

        # Anti-hallucination check
        has_evidence = check_evidence_strength(chunks)

        if not has_evidence:
            logger.warning(
                f"Insufficient evidence | "
                f"query={data.query[:50]}"
            )
            return {
                "question":     data.query,
                "answer":       NO_ANSWER,
                "citations":    [],
                "chunks":       [],
                "has_evidence": False,
                "confidence":   0.0,
                "session_id":   data.session_id
            }

        # Build context and citations
        citations      = build_citations(chunks)
        context        = build_context_string(chunks)
        citation_text  = format_citations_for_prompt(citations)
        full_context   = context + citation_text

        # Get session history from Redis
        session      = get_session(data.session_id) or {}
        chat_history = session.get(
            "history",
            "No previous conversation."
        )

        # Generate answer via LangChain
        chain    = ANSWER_PROMPT | llm
        response = chain.invoke({
            "question":     data.query,
            "context":      full_context,
            "chat_history": chat_history
        })
        answer = response.content

        # Update session memory in Redis
        new_history = (
            f"{chat_history}\n"
            f"User: {data.query}\n"
            f"Assistant: {answer[:300]}..."
        )
        session["history"] = new_history[-3000:]
        cache_session(data.session_id, session, CACHE_TTL_SESSION)

        # Calculate confidence
        avg_confidence = get_avg_confidence(chunks)

        # Save to PostgreSQL
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO citerag_sessions
                (session_id, question, answer,
                 citations, confidence, filters_used)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    data.session_id,
                    data.query,
                    answer,
                    json.dumps(citations),
                    avg_confidence,
                    json.dumps(data.filters or {})
                )
            )
            conn.commit()
        finally:
            cursor.close()
            release_connection(conn)

        logger.info(
            f"Answer generated | "
            f"session={data.session_id} | "
            f"confidence={avg_confidence}"
        )

        return {
            "question":     data.query,
            "answer":       answer,
            "citations":    citations,
            "chunks":       chunks,
            "has_evidence": True,
            "confidence":   avg_confidence,
            "session_id":   data.session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))