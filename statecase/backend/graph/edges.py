def route_after_clarify(state: dict) -> str:
    """
    Route after clarification check.
    If needs clarification → return clarify state
    If clear → go to retrieve
    """
    if state.get("needs_clarification"):
        return "clarify"
    return "retrieve"


def route_after_retrieve(state: dict) -> str:
    """
    Route after CiteRAG retrieval.
    If evidence found → go to answer
    If no evidence → go to create ticket
    """
    if state.get("has_evidence"):
        return "answer"
    return "insufficient"