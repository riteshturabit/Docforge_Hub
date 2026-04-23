import logging
import requests
from statecase.backend.llm import llm
from statecase.backend.prompts.clarify_prompt import CLARIFY_PROMPT
from statecase.backend.constants import (
    CITERAG_API_URL,
    CITERAG_TOP_K,
    STATE_CLARIFY,
    STATE_RETRIEVE,
    STATE_ANSWER,
    STATE_TICKET,
    STATE_DONE
)

logger = logging.getLogger("statecase.nodes")


def node_clarify(state: dict) -> dict:
    """
    Node 1 — CLARIFY
    Only ask clarification if question is vague
    AND no clarification was already asked!
    If user is answering a clarification → skip to retrieve!
    """
    message     = state["message"]
    history     = state.get("history", "No previous conversation.")
    last_action = state.get("last_action", "")

    # If last action was clarification question
    # → User is now answering it → skip to retrieve!
    if last_action == "clarification_question":
        state["needs_clarification"] = False
        state["refined_intent"]      = message
        state["current_state"]       = STATE_RETRIEVE
        logger.info(
            f"Clarification answered | "
            f"session={state['session_id']}"
        )
        return state

    # Normal clarification check
    chain    = CLARIFY_PROMPT | llm
    response = chain.invoke({
        "message": message,
        "history": history
    })
    result = response.content.strip()

    if result.startswith("CLARIFY:"):
        question = result.replace("CLARIFY:", "").strip()
        state["needs_clarification"]    = True
        state["clarification_question"] = question
        state["current_state"]          = STATE_CLARIFY
        logger.info(
            f"Clarification needed | "
            f"session={state['session_id']}"
        )
    else:
        intent = result.replace("CLEAR:", "").strip()
        state["needs_clarification"] = False
        state["refined_intent"]      = intent
        state["current_state"]       = STATE_RETRIEVE
        logger.info(
            f"Intent clear | "
            f"session={state['session_id']}"
        )

    return state


def node_retrieve(state: dict) -> dict:
    """
    Node 2 — RETRIEVE
    Call CiteRAG API to get grounded answer.

    Sets:
    → answer, citations, confidence
    → has_evidence = True/False
    → current_state = "answer" or "create_ticket"
    """
    query    = state.get("refined_intent") or state["message"]
    industry = state.get("user_industry", "General")

    filters = {}
    if industry and industry != "General":
        filters["industry"] = industry

    try:
        resp = requests.post(
            f"{CITERAG_API_URL}/answer",
            json={
                "query":      query,
                "session_id": state["session_id"],
                "top_k":      CITERAG_TOP_K,
                "filters":    filters if filters else None
            },
            timeout=60
        )
        data = resp.json()

        state["answer"]       = data.get("answer", "")
        state["citations"]    = data.get("citations", [])
        state["confidence"]   = data.get("confidence", 0.0)
        state["has_evidence"] = data.get("has_evidence", False)
        state["chunks"]       = data.get("chunks", [])

        if state["has_evidence"]:
            state["current_state"] = STATE_ANSWER
        else:
            state["current_state"] = STATE_TICKET

        logger.info(
            f"Retrieval done | "
            f"evidence={state['has_evidence']} | "
            f"session={state['session_id']}"
        )

    except Exception as e:
        logger.error(f"Retrieval node failed | {e}")
        state["has_evidence"]  = False
        state["current_state"] = STATE_TICKET
        state["citations"]     = []
        state["chunks"]        = []

    return state


def node_answer(state: dict) -> dict:
    """
    Node 3 — ANSWER
    Format and return the grounded answer.

    Sets:
    → reply = final answer text
    → current_state = "done"
    """
    state["reply"]         = state.get("answer", "No answer generated")
    state["current_state"] = STATE_DONE

    logger.info(
        f"Answer node complete | "
        f"session={state['session_id']}"
    )
    return state


def node_insufficient(state: dict) -> dict:
    """
    Node 4 — CREATE TICKET
    Handle case where CiteRAG has no answer.
    Generate professional response explaining ticket creation.

    Sets:
    → reply = professional message about ticket
    → current_state = "create_ticket"
    """
    question = state["message"]

    state["reply"] = (
        f"I was unable to find sufficient information "
        f"about '{question[:100]}' in the current "
        f"document library.\n\n"
        f"I have automatically created a support ticket "
        f"for this query. The relevant team will review "
        f"it and update the knowledge base accordingly.\n\n"
        f"You can track the ticket status in "
        f"**My Tickets** page."
    )
    state["current_state"] = STATE_TICKET

    logger.info(
        f"Insufficient evidence | "
        f"session={state['session_id']}"
    )
    return state