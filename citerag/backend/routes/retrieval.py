import hashlib
import logging
from fastapi import APIRouter, HTTPException
from citerag.backend.models.retrieval_models import (
    RetrievalRequest,
    RetrievalResponse
)
from citerag.backend.rag.retriever import retrieve_chunks
from citerag.backend.rag.citations import build_citations
from citerag.backend.redis_client import (
    cache_set,
    cache_get
)
from citerag.backend.constants import CACHE_TTL_RETRIEVAL

router = APIRouter()
logger = logging.getLogger("citerag.routes.retrieval")


@router.post("/retrieve")
def retrieve(data: RetrievalRequest):
    """
    Retrieve relevant chunks from Qdrant.

    Flow:
    1. Build cache key from query + filters
    2. Check Redis cache
    3. If miss → search Qdrant
    4. Build citations
    5. Cache and return results
    """

    # Build unique cache key
    cache_key = hashlib.md5(
        f"{data.query}{data.filters}{data.top_k}".encode()
    ).hexdigest()
    cache_key = f"citerag:retrieval:{cache_key}"

    # Check Redis cache first
    cached = cache_get(cache_key)
    if cached:
        logger.info(f"Cache HIT | query={data.query[:40]}")
        return cached

    try:
        chunks    = retrieve_chunks(
            data.query,
            data.top_k,
            data.filters
        )
        citations = build_citations(chunks)

        result = {
            "query":     data.query,
            "chunks":    chunks,
            "citations": citations,
            "total":     len(chunks),
            "filters":   data.filters or {}
        }

        # Cache result
        cache_set(cache_key, result, CACHE_TTL_RETRIEVAL)

        logger.info(
            f"Retrieval done | "
            f"chunks={len(chunks)} | "
            f"query={data.query[:40]}"
        )
        return result

    except Exception as e:
        logger.error(f"Retrieval failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrieve/filters")
def get_available_filters():
    """
    Get all available filter values from PostgreSQL
    Used to populate filter dropdowns in frontend
    """
    from citerag.backend.database import get_connection, release_connection
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT DISTINCT industry FROM citerag_chunks WHERE industry != ''"
        )
        industries = [r[0] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT doc_type FROM citerag_chunks WHERE doc_type != ''"
        )
        doc_types = [r[0] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT version FROM citerag_chunks WHERE version != ''"
        )
        versions = [r[0] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT doc_title FROM citerag_chunks"
        )
        doc_titles = [r[0] for r in cursor.fetchall()]

        return {
            "industries": industries,
            "doc_types":  doc_types,
            "versions":   versions,
            "doc_titles": doc_titles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)