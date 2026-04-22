import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)
from citerag.backend.llm import embeddings
from citerag.backend.constants import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    DEFAULT_TOP_K,
    MIN_CONFIDENCE
)

logger = logging.getLogger("citerag.retriever")

client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def build_qdrant_filter(filters: dict) -> Filter:
    if not filters:
        return None

    conditions = []

    if filters.get("industry"):
        conditions.append(
            FieldCondition(
                key="industry",
                match=MatchValue(value=filters["industry"])
            )
        )

    if filters.get("doc_type"):
        conditions.append(
            FieldCondition(
                key="doc_type",
                match=MatchValue(value=filters["doc_type"])
            )
        )

    if filters.get("version"):
        conditions.append(
            FieldCondition(
                key="version",
                match=MatchValue(value=filters["version"])
            )
        )

    if filters.get("doc_title"):
        conditions.append(
            FieldCondition(
                key="doc_title",
                match=MatchValue(value=filters["doc_title"])
            )
        )

    return Filter(must=conditions) if conditions else None


def retrieve_chunks(
    query:   str,
    top_k:   int  = DEFAULT_TOP_K,
    filters: dict = None
) -> list:
    try:
        query_vector  = embeddings.embed_query(query)
        qdrant_filter = build_qdrant_filter(filters)

        results = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
            with_vectors=False
        ).points

        chunks = []
        for r in results:
            chunks.append({
                "qdrant_id":      r.id,
                "score":          round(r.score, 4),
                "confidence":     round(r.score * 100, 1),
                "doc_title":      r.payload.get("doc_title", ""),
                "section_title":  r.payload.get("section_title", ""),
                "chunk_text":     r.payload.get("chunk_text", ""),
                "notion_page_id": r.payload.get("notion_page_id", ""),
                "industry":       r.payload.get("industry", ""),
                "doc_type":       r.payload.get("doc_type", ""),
                "version":        r.payload.get("version", ""),
                "chunk_index":    r.payload.get("chunk_index", 0),
            })

        logger.info(
            f"Retrieved {len(chunks)} chunks | "
            f"query={query[:50]} | filters={filters}"
        )
        return chunks

    except Exception as e:
        logger.error(f"Retrieval failed | {e}")
        raise


def retrieve_for_compare(
    doc_title_1: str,
    doc_title_2: str,
    query:       str,
    top_k:       int = 3
) -> dict:
    try:
        query_vector = embeddings.embed_query(query)

        def fetch_doc(title: str) -> list:
            results = client.query_points(
                collection_name=QDRANT_COLLECTION,
                query=query_vector,
                limit=top_k,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_title",
                            match=MatchValue(value=title)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            ).points
            return [{
                "doc_title":     r.payload.get("doc_title", ""),
                "section_title": r.payload.get("section_title", ""),
                "chunk_text":    r.payload.get("chunk_text", ""),
                "score":         round(r.score, 4),
                "confidence":    round(r.score * 100, 1),
            } for r in results]

        doc1_chunks = fetch_doc(doc_title_1)
        doc2_chunks = fetch_doc(doc_title_2)

        logger.info(
            f"Compare retrieval | "
            f"doc1={doc_title_1} | doc2={doc_title_2}"
        )
        return {
            "doc1": doc1_chunks,
            "doc2": doc2_chunks
        }

    except Exception as e:
        logger.error(f"Compare retrieval failed | {e}")
        raise


def check_evidence_strength(
    chunks:    list,
    threshold: float = MIN_CONFIDENCE
) -> bool:
    if not chunks:
        return False

    avg_score = sum(
        c.get("score", 0) for c in chunks
    ) / len(chunks)

    has_evidence = avg_score >= threshold

    logger.debug(
        f"Evidence check | "
        f"avg_score={avg_score:.3f} | "
        f"threshold={threshold} | "
        f"has_evidence={has_evidence}"
    )
    return has_evidence