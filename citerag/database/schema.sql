-- CiteRAG Lab Database Schema

-- Ingested document chunks
CREATE TABLE IF NOT EXISTS citerag_chunks (
    id              SERIAL PRIMARY KEY,
    notion_page_id  VARCHAR(200) NOT NULL,
    doc_title       VARCHAR(300) NOT NULL,
    section_title   VARCHAR(300),
    chunk_text      TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    industry        VARCHAR(100),
    doc_type        VARCHAR(100),
    version         VARCHAR(20)  DEFAULT 'v1.0',
    qdrant_id       VARCHAR(200),
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_notion_page
ON citerag_chunks(notion_page_id);

CREATE INDEX IF NOT EXISTS idx_chunks_doc_title
ON citerag_chunks(doc_title);

-- Q&A session history
CREATE TABLE IF NOT EXISTS citerag_sessions (
    id           SERIAL PRIMARY KEY,
    session_id   VARCHAR(200) UNIQUE NOT NULL,
    question     TEXT,
    answer       TEXT,
    citations    JSONB,
    confidence   FLOAT,
    filters_used JSONB,
    created_at   TIMESTAMP DEFAULT NOW()
);

-- RAGAS evaluation runs
CREATE TABLE IF NOT EXISTS citerag_eval_runs (
    id                SERIAL PRIMARY KEY,
    run_name          VARCHAR(200),
    config            JSONB,
    dataset           JSONB,
    results           JSONB,
    faithfulness      FLOAT,
    answer_relevancy  FLOAT,
    context_precision FLOAT,
    created_at        TIMESTAMP DEFAULT NOW()
);