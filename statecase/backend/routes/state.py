import logging
from fastapi import APIRouter, HTTPException
from statecase.backend.graph.memory import (
    load_session,
    load_messages,
    save_session
)
from statecase.backend.database import get_connection, release_connection

router = APIRouter()
logger = logging.getLogger("statecase.state")


@router.get("/state/{session_id}")
def get_session_state(session_id: str):
    """Get current session state"""
    try:
        state = load_session(session_id)
        return {
            "session_id":    session_id,
            "state":         state.get("state", "idle"),
            "user_industry": state.get("user_industry", "General"),
            "intent":        state.get("current_intent"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/state/{session_id}")
def reset_session(session_id: str):
    """Reset session state to idle"""
    try:
        save_session(session_id, {
            "session_id":     session_id,
            "user_industry":  "General",
            "current_intent": None,
            "state":          "idle",
            "last_retrieved": None
        })
        logger.info(f"Session reset | session={session_id}")
        return {"message": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/history/{session_id}")
def get_conversation_history(session_id: str):
    """Get full conversation history"""
    try:
        messages = load_messages(session_id)
        return {
            "session_id": session_id,
            "messages":   messages,
            "total":      len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))