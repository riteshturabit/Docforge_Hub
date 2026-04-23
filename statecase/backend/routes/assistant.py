import logging
from fastapi import APIRouter, HTTPException
from statecase.backend.models.chat_models import (
    ChatRequest,
    StateResponse
)
from statecase.backend.graph.nodes import (
    node_clarify,
    node_retrieve,
    node_answer,
    node_insufficient
)
from statecase.backend.graph.edges import (
    route_after_clarify,
    route_after_retrieve
)
from statecase.backend.graph.memory import (
    load_session,
    save_session,
    load_messages,
    save_message
)
from statecase.backend.routes.tickets import create_ticket
from statecase.backend.models.ticket_models import TicketRequest
from statecase.backend.utils.ticket_utils import (
    build_ticket_summary,
    format_sources_tried
)
from statecase.backend.redis_client import check_rate_limit
from statecase.backend.constants import (
    RATE_LIMIT_CHAT,
    RATE_LIMIT_WINDOW,
    MEMORY_RECENT_MESSAGES
)

router = APIRouter()
logger = logging.getLogger("statecase.assistant")


@router.post("/chat", response_model=StateResponse)
def chat(data: ChatRequest):
    """
    Main LangGraph orchestration endpoint.

    Flow:
    1. Load session + message history
    2. Run clarify node
    3. If needs clarification → return question
    4. Run retrieve node (calls CiteRAG)
    5. If has evidence → run answer node → return
    6. If no evidence → run ticket node → create ticket
    """

    # Rate limiting
    if not check_rate_limit(
        f"chat_{data.session_id}",
        max_calls=RATE_LIMIT_CHAT,
        window=RATE_LIMIT_WINDOW
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait."
        )

    logger.info(
        f"Chat request | "
        f"session={data.session_id} | "
        f"msg={data.message[:50]}"
    )

    # Load session and history
    session  = load_session(data.session_id)
    messages = load_messages(data.session_id)

    # Update industry if provided
    if data.industry:
        session["user_industry"] = data.industry

    # Build history string for prompts
    history = "\n".join([
        f"{m['role'].title()}: {m['content']}"
        for m in messages[-MEMORY_RECENT_MESSAGES:]
    ])

    # Build LangGraph state
    graph_state = {
        "session_id":    data.session_id,
        "message":       data.message,
        "history":       history or "No previous conversation.",
        "user_industry": session.get("user_industry", "General"),
        "current_state": "start",
        "last_action":   session.get("last_action", ""),  # ← Track last action
    }

    # ── Node 1: Clarify ───────────────────────────────────────
    graph_state = node_clarify(graph_state)
    route       = route_after_clarify(graph_state)

    if route == "clarify":
        save_message(data.session_id, "user", data.message)
        save_message(
            data.session_id,
            "assistant",
            graph_state["clarification_question"]
        )
        session["state"]       = "clarify"
        session["last_action"] = "clarification_question"  # ← Save action
        save_session(data.session_id, session)

        return StateResponse(
            session_id=data.session_id,
            reply=graph_state["clarification_question"],
            state="clarify",
            citations=[],
            needs_clarification=True,
            clarification_question=graph_state["clarification_question"],
            confidence=0.0
        )

    # ── Node 2: Retrieve ──────────────────────────────────────
    graph_state = node_retrieve(graph_state)
    route       = route_after_retrieve(graph_state)

    if route == "answer":
        # ── Node 3: Answer ────────────────────────────────────
        graph_state = node_answer(graph_state)

        save_message(data.session_id, "user", data.message)
        save_message(data.session_id, "assistant", graph_state["reply"])
        session["state"]          = "done"
        session["last_action"]    = "retrieve"  # ← Reset action
        session["last_retrieved"] = graph_state.get("citations", [])
        save_session(data.session_id, session)

        return StateResponse(
            session_id=data.session_id,
            reply=graph_state["reply"],
            state="answered",
            citations=graph_state.get("citations", []),
            confidence=graph_state.get("confidence", 0.0)
        )

    else:
        # ── Node 4: Insufficient → Create Ticket ─────────────
        graph_state = node_insufficient(graph_state)
        ticket_id   = None
        notion_url  = None

        try:
            sources_tried = format_sources_tried(
                graph_state.get("citations", [])
            )
            ticket_data = build_ticket_summary(
                question=data.message,
                history=history,
                sources_tried=sources_tried
            )

            ticket_req = TicketRequest(
                session_id=data.session_id,
                question=data.message,
                sources_tried=sources_tried,
                summary=ticket_data["summary"],
                priority=ticket_data["priority"],
                assigned_owner="Support Team"
            )
            ticket_result = create_ticket(ticket_req)
            ticket_id     = ticket_result.notion_ticket_id
            notion_url    = ticket_result.notion_url

        except Exception as e:
            logger.error(f"Ticket creation failed | {e}")

        save_message(data.session_id, "user", data.message)
        save_message(data.session_id, "assistant", graph_state["reply"])
        session["state"]       = "ticket_created"
        session["last_action"] = "ticket"  # ← Reset action
        save_session(data.session_id, session)

        return StateResponse(
            session_id=data.session_id,
            reply=graph_state["reply"],
            state="ticket_created",
            citations=[],
            ticket_id=ticket_id,
            confidence=0.0
        )