#import json
import re
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.llm import llm

router = APIRouter()


def clean_chat_response(text: str) -> str:
    """Remove all markdown from chat response."""
    import re
    # Remove ### ## # headings
    text = re.sub(r'#{1,6}\s*', '', text)
    # Remove --- dividers
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    # Remove *** dividers
    text = re.sub(r'^\*\*\*+$', '', text, flags=re.MULTILINE)
    # Convert **bold** to plain text — keep the word just remove **
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove single * italic
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove __ underline
    text = re.sub(r'__(.*?)__', r'\1', text)
    # Remove backticks
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)
    # Clean extra blank lines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

CHAT_PROMPT = PromptTemplate(
    input_variables=["document_title", "document_content", "chat_history", "user_question"],
    template="""
You are an expert document analyst assistant for DocForge Hub.
You have been given a complete enterprise document to analyze and answer questions about.

Document Title: {document_title}

Full Document Content:
{document_content}

Previous conversation:
{chat_history}

User Question: {user_question}

Instructions:
- Answer ONLY based on the document content above
- When asked to summarize: give a CONCISE summary in maximum 8-10 bullet points
  covering the entire document — do NOT summarize section by section
  — pick only the most important points across the whole document
- When asked what is missing: give maximum 5 key gaps only — most important ones
- When asked for key points: give maximum 8 bullet points — most critical points only
- When asked for risks: give maximum 5 key risks — most impactful ones only
- Keep all answers SHORT and CRISP — quality over quantity
- Never give section by section breakdown unless user explicitly asks for it
- Be specific and reference exact sections when relevant
- If the question is not related to the document, politely redirect
- Keep answers clear, professional and well structured
- Do not make up information not in the document

STRICT FORMATTING RULES — follow exactly:
- Do NOT use ### or ## or # for headings
- Do NOT use --- or *** as dividers
- Do NOT use ** for bold — instead write the label naturally followed by colon
- Do NOT use markdown formatting of any kind
- For section titles or labels write them plainly followed by colon like: Section 1 Overview:
- For bullet points use only this symbol: •
- For sub bullets use: -
- Keep answers clean with no special characters
- Separate sections with a single blank line only
- Numbers for numbered lists like: 1. 2. 3.

Answer:
"""
)

@router.post("/chat_document")
def chat_document(data: dict[str, object]) -> dict[str, str]:
    document_id  = data.get("document_id")
    user_question = data.get("question", "").strip()
    chat_history  = data.get("chat_history", [])

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id required")
    if not user_question:
        raise HTTPException(status_code=400, detail="question required")

    conn   = get_connection()
    cursor = conn.cursor()

    # Get document title
    cursor.execute(
        """
        SELECT dt.name FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        WHERE d.id = %s
        """,
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    document_title = result[0]

    # Get all sections
    cursor.execute(
        """
        SELECT DISTINCT ON (section_order)
            section_title, section_content, section_order
        FROM document_sections
        WHERE document_id=%s
        ORDER BY section_order, id DESC
        """,
        (document_id,)
    )
    sections = cursor.fetchall()
    cursor.close()
    conn.close()

    if not sections:
        raise HTTPException(
            status_code=400,
            detail="Document has no content yet. Generate sections first."
        )

    # Build full document content
    document_content = "\n\n".join([
        f"Section {s[2]} — {s[0]}:\n{s[1]}"
        for s in sections
    ])

    # Build chat history string
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Last 3 exchanges
            role    = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"User: {content}\n"
            elif role == "assistant":
                history_text += f"Assistant: {content}\n"

    # Build chain
    chain = CHAT_PROMPT | llm

    try:
        response = chain.invoke({
            "document_title":   document_title,
            "document_content": document_content[:20000],  # Limit to avoid token overflow
            "chat_history":     history_text or "No previous conversation.",
            "user_question":    user_question
        })
        raw_content = response.content
        answer = clean_chat_response(
            str(raw_content) if not isinstance(raw_content, str)
            else raw_content or "I could not generate an answer. Please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )

    return {
        "question": user_question,
        "answer":   answer,
        "document": document_title
    }