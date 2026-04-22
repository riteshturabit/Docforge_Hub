import logging
from statecase.backend.llm import llm
from statecase.backend.prompts.ticket_prompt import TICKET_PROMPT

logger = logging.getLogger("statecase.utils.ticket")


def parse_ticket_response(response_text: str) -> dict:
    """
    Parse LLM ticket prompt response into summary + priority

    Expected format:
    SUMMARY: Professional description here
    PRIORITY: High
    """
    summary  = "User question could not be answered from document library."
    priority = "Medium"

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("PRIORITY:"):
            raw = line.replace("PRIORITY:", "").strip()
            if raw in ["High", "Medium", "Low"]:
                priority = raw

    return {
        "summary":  summary,
        "priority": priority
    }


def build_ticket_summary(
    question:      str,
    history:       str,
    sources_tried: list
) -> dict:
    """
    Use LLM to generate professional ticket summary
    and auto-detect priority
    """
    try:
        sources_text = (
            ", ".join(sources_tried)
            if sources_tried
            else "No relevant sources found"
        )

        chain    = TICKET_PROMPT | llm
        response = chain.invoke({
            "question":      question,
            "history":       history,
            "sources_tried": sources_text
        })

        result = parse_ticket_response(response.content)
        logger.info(
            f"Ticket summary built | "
            f"priority={result['priority']}"
        )
        return result

    except Exception as e:
        logger.error(f"Ticket summary failed | {e}")
        return {
            "summary":  f"User asked: {question[:200]}",
            "priority": "Medium"
        }


def format_sources_tried(citations: list) -> list:
    """
    Extract display names from citations list
    Used in ticket to show what was searched
    """
    if not citations:
        return []
    return [
        c.get("display", "")
        for c in citations
        if c.get("display")
    ]