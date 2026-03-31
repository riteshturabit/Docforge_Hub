from fastapi import FastAPI
from dotenv import load_dotenv
from backend.redis_client import redis_health,get_job_status
from backend.routes import chat
from backend.routes import versioning


load_dotenv()

from backend.routes import (
    departments,
    templates,
    company,
    documents,
    questions,
    sections,
    enhance,
    downloads,
    notion,
    scoring,
    suggestions
)

app = FastAPI(title="DocForge Hub API", version="1.0.0")

app.include_router(departments.router, tags=["Departments"])
app.include_router(templates.router,   tags=["Templates"])
app.include_router(company.router,     tags=["Company"])
app.include_router(documents.router,   tags=["Documents"])
app.include_router(questions.router,   tags=["Questions"])
app.include_router(sections.router,    tags=["Sections"])
app.include_router(enhance.router,     tags=["Enhance"])
app.include_router(downloads.router,   tags=["Downloads"])
app.include_router(notion.router,      tags=["Notion"])
app.include_router(scoring.router,     tags=["Scoring"])
app.include_router(suggestions.router, tags=["Suggestions"])
app.include_router(chat.router,        tags=["Chat"]) 
app.include_router(versioning.router,  tags=["Versioning"])


@app.get("/")
def home():
    return {"message": "DocForge API Running"}

@app.get("/health")
def health_check():
    return {
        "api":   "running",
        "redis": "connected" if redis_health() else "disconnected"
    }

@app.get("/job/{job_id}")
def get_job(job_id: str) -> dict:
    return get_job_status(job_id)