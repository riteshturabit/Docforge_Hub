import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from citerag.backend.routes import (
    ingest,
    retrieval,
    answer,
    tools,
    evaluate
)

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/citerag.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("citerag.main")

app = FastAPI(
    title="CiteRAG Lab API",
    description="RAG-powered document Q&A with citations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(ingest.router,    tags=["Ingestion"])
app.include_router(retrieval.router, tags=["Retrieval"])
app.include_router(answer.router,    tags=["Answer"])
app.include_router(tools.router,     tags=["Tools"])
app.include_router(evaluate.router,  tags=["Evaluation"])


@app.get("/health")
def health():
    return {
        "status":  "ok",
        "service": "CiteRAG Lab",
        "port":    8001
    }


@app.get("/")
def home():
    return {"message": "CiteRAG Lab API Running"}


logger.info("CiteRAG Lab API started on port 8001")