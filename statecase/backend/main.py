import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from statecase.backend.routes import assistant, tickets, state

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/statecase.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("statecase.main")

app = FastAPI(
    title="StateCase Assistant API",
    description="Stateful AI assistant with LangGraph + Notion ticketing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(assistant.router, tags=["Assistant"])
app.include_router(tickets.router,   tags=["Tickets"])
app.include_router(state.router,     tags=["State"])


@app.get("/health")
def health():
    return {
        "status":  "ok",
        "service": "StateCase Assistant",
        "port":    8002
    }


@app.get("/")
def home():
    return {"message": "StateCase Assistant API Running"}


logger.info("StateCase Assistant API started on port 8002")