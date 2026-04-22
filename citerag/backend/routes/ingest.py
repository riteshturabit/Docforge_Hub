import logging
from fastapi import APIRouter, HTTPException
from citerag.backend.models.ingest_models import (
    IngestRequest,
    IngestResponse
)
from citerag.backend.rag.chunker import (
    get_notion_pages,
    extract_page_content,
    extract_page_metadata,
    blocks_to_chunks
)
from citerag.backend.rag.embedder import (
    embed_and_store,
    delete_page_vectors
)
from citerag.backend.redis_client import check_rate_limit
from citerag.backend.database import get_connection, release_connection

router = APIRouter()
logger = logging.getLogger("citerag.routes.ingest")


@router.post("/ingest", response_model=IngestResponse)
def ingest_notion_docs(data: IngestRequest):
    """
    Ingest all Notion documents into Qdrant vector store.

    Flow:
    1. Fetch all pages from Notion database
    2. For each page → extract blocks
    3. Convert blocks → chunks
    4. Embed chunks → store in Qdrant
    5. Save chunk metadata → PostgreSQL
    """
    logger.info(f"Ingestion started | db={data.database_id}")

    # Rate limit Notion reads
    if not check_rate_limit(
        "notion_ingest",
        max_calls=5,
        window=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Ingestion rate limit exceeded. Please wait."
        )

    conn   = get_connection()
    cursor = conn.cursor()

    try:
        pages        = get_notion_pages(data.database_id)
        total_chunks = 0
        pages_done   = 0

        for page in pages:
            page_id  = page["id"]
            metadata = extract_page_metadata(page)

            if not metadata.get("doc_title"):
                logger.warning(f"Skipping page with no title | page={page_id}")
                continue

            # Skip if already ingested and not force
            if not data.force_reingest:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM citerag_chunks
                    WHERE notion_page_id=%s
                    """,
                    (page_id,)
                )
                if cursor.fetchone()[0] > 0:
                    logger.info(f"Already ingested | page={page_id}")
                    continue

            # Force reingest → delete old vectors
            if data.force_reingest:
                delete_page_vectors(page_id)
                cursor.execute(
                    "DELETE FROM citerag_chunks WHERE notion_page_id=%s",
                    (page_id,)
                )

            # Extract blocks and chunk
            blocks = extract_page_content(page_id)
            chunks = blocks_to_chunks(blocks, page_id, metadata)

            if not chunks:
                logger.warning(f"No chunks | page={page_id}")
                continue

            # Embed and store in Qdrant
            qdrant_ids = embed_and_store(chunks)

            # Save chunk metadata to PostgreSQL
            for chunk, qid in zip(chunks, qdrant_ids):
                cursor.execute(
                    """
                    INSERT INTO citerag_chunks
                    (notion_page_id, doc_title, section_title,
                     chunk_text, chunk_index, industry,
                     doc_type, version, qdrant_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        chunk["notion_page_id"],
                        chunk["doc_title"],
                        chunk["section_title"],
                        chunk["chunk_text"],
                        chunk["chunk_index"],
                        chunk["industry"],
                        chunk["doc_type"],
                        chunk["version"],
                        qid
                    )
                )
            total_chunks += len(chunks)
            pages_done   += 1

        conn.commit()
        logger.info(
            f"Ingestion complete | "
            f"pages={pages_done} | chunks={total_chunks}"
        )

        return IngestResponse(
            status="success",
            pages_ingested=pages_done,
            total_chunks=total_chunks,
            message=f"Ingested {pages_done} pages into {total_chunks} chunks"
        )

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Ingestion failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)


@router.get("/ingest/status")
def get_ingest_status():
    """Get current ingestion status from PostgreSQL"""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*)                    as total_chunks,
                COUNT(DISTINCT notion_page_id) as total_docs,
                COUNT(DISTINCT doc_type)    as doc_types,
                COUNT(DISTINCT industry)    as industries
            FROM citerag_chunks
            """
        )
        row = cursor.fetchone()
        return {
            "total_chunks":  row[0],
            "total_docs":    row[1],
            "doc_types":     row[2],
            "industries":    row[3],
            "status":        "ready" if row[0] > 0 else "empty"
        }
    except Exception as e:
        logger.error(f"Status check failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)