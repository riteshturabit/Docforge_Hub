import re
import logging

logger = logging.getLogger("citerag.utils.text")


def clean_notion_text(text: str) -> str:
    """Clean raw text extracted from Notion blocks"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def truncate_text(text: str, max_length: int = 500) -> str:
    """Safely truncate text to max length"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    # Cut at last complete word
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def build_context_string(chunks: list) -> str:
    """
    Build formatted context string from chunks
    for LLM prompt injection
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_title     = chunk.get("doc_title", "Unknown")
        section_title = chunk.get("section_title", "General")
        chunk_text    = chunk.get("chunk_text", "")

        context_parts.append(
            f"[{i}] {doc_title} → {section_title}:\n"
            f"{chunk_text}"
        )

    return "\n\n".join(context_parts)