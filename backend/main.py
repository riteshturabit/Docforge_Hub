from fastapi import FastAPI
from dotenv import load_dotenv

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
    notion
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


@app.get("/")
def home():
    return {"message": "DocForge API Running"}