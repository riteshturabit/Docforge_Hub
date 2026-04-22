import logging
from fastapi import APIRouter, HTTPException
from citerag.backend.llm import llm
from citerag.backend.rag.retriever import (
    retrieve_chunks,
    retrieve_for_compare
)
from citerag.backend.rag.citations import build_citations
from citerag.backend.prompts.refine_prompt import REFINE_PROMPT
from citerag.backend.prompts.compare_prompt import COMPARE_PROMPT
from citerag.backend.models.retrieval_models import RetrievalRequest

router = APIRouter()
logger = logging.getLogger("citerag.routes.tools")


@router.post("/tools/search")
def smart_search(data: RetrievalRequest):
    """
    Tool 1 — Smart semantic search with filters
    Returns chunks + citations
    """
    try:
        chunks    = retrieve_chunks(
            data.query,
            data.top_k,
            data.filters
        )
        citations = build_citations(chunks)

        logger.info(f"Smart search | query={data.query[:40]}")
        return {
            "query":     data.query,
            "chunks":    chunks,
            "citations": citations,
            "total":     len(chunks)
        }
    except Exception as e:
        logger.error(f"Smart search failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/refine")
def refine_query(original_query: str, feedback: str):
    """
    Tool 2 — Refine vague query using feedback

    Example:
    original: "payment"
    feedback: "need vendor late payment penalty info"
    refined:  "vendor late payment penalty clause finance"
    """
    try:
        chain    = REFINE_PROMPT | llm
        response = chain.invoke({
            "original_query": original_query,
            "feedback":       feedback
        })
        refined = response.content.strip()

        logger.info(
            f"Query refined | "
            f"original={original_query[:40]}"
        )
        return {
            "original_query": original_query,
            "feedback":       feedback,
            "refined_query":  refined
        }
    except Exception as e:
        logger.error(f"Query refine failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/compare")
def compare_documents(
    query:       str,
    doc_title_1: str,
    doc_title_2: str
):
    """
    Tool 3 — Compare two documents on a query

    Example:
    query: "payment terms"
    doc1: "SOW Agreement"
    doc2: "Master Service Agreement"
    → Side by side comparison with recommendation
    """
    try:
        results = retrieve_for_compare(
            doc_title_1,
            doc_title_2,
            query
        )

        doc1_content = "\n".join(
            [c["chunk_text"] for c in results["doc1"]]
        ) or "No relevant content found"

        doc2_content = "\n".join(
            [c["chunk_text"] for c in results["doc2"]]
        ) or "No relevant content found"

        chain    = COMPARE_PROMPT | llm
        response = chain.invoke({
            "query":        query,
            "doc1_title":   doc_title_1,
            "doc1_content": doc1_content,
            "doc2_title":   doc_title_2,
            "doc2_content": doc2_content
        })

        logger.info(
            f"Compare done | "
            f"doc1={doc_title_1} | doc2={doc_title_2}"
        )
        return {
            "query":       query,
            "doc1_title":  doc_title_1,
            "doc2_title":  doc_title_2,
            "comparison":  response.content,
            "doc1_chunks": results["doc1"],
            "doc2_chunks": results["doc2"]
        }
    except Exception as e:
        logger.error(f"Compare failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))