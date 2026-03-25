from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.llm import llm

router = APIRouter()

ACTION_MAP = {
    "longer":   "Make the content more detailed and comprehensive",
    "shorter":  "Make the content shorter and to the point",
    "formal":   "Make the tone more formal and professional",
    "concise":  "Make the content concise without losing meaning",
    "examples": "Add relevant real-world examples",
    "table":    "Restructure content into a well-formatted table using pipe format",
    "clarity":  "Improve clarity and readability",
    "grammar":  "Fix grammar and improve sentence structure"
}

ENHANCE_SECTION_PROMPT = PromptTemplate(
    input_variables=[
        "section_title", "content",
        "instruction", "custom_instruction"
    ],
    template="""
You are an expert enterprise document editor.

Section: {section_title}

Current Content:
{content}

Enhancement Instruction: {instruction}
{custom_instruction}

Rules:
- Keep the core meaning intact
- Improve quality only
- Do not add fake policies or assumptions
- Do not use markdown symbols like ##, **, __
- Write in clean plain paragraphs
- If using a table use proper pipe format like | Col1 | Col2 |

Return only the improved content:
"""
)

ENHANCE_DOCUMENT_PROMPT = PromptTemplate(
    input_variables=[
        "instruction", "custom_instruction", "full_text"
    ],
    template="""
You are an expert enterprise document editor.

Enhancement Instruction: {instruction}
{custom_instruction}

Full Document:
{full_text}

Rules:
- Keep core meaning intact
- Improve quality consistently across all sections
- Do not use markdown symbols
- Return only the improved document

Return improved document:
"""
)


@router.post("/enhance_section")
def enhance_section(data: dict):
    conn   = get_connection()
    cursor = conn.cursor()

    document_id        = data.get("document_id")
    section_order      = data.get("section_order")
    action             = data.get("action")
    custom_instruction = data.get("custom_instruction", "")

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id required")

    instruction = ACTION_MAP.get(action, "Improve the content quality")

    if section_order is not None:
        cursor.execute(
            """
            SELECT section_title, section_content
            FROM document_sections
            WHERE document_id=%s AND section_order=%s
            """,
            (document_id, section_order)
        )
        section = cursor.fetchone()
        if not section:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Section not found")

        section_title, content = section
        chain = ENHANCE_SECTION_PROMPT | llm

        try:
            response = chain.invoke({
                "section_title":      section_title,
                "content":            content,
                "instruction":        instruction,
                "custom_instruction": custom_instruction
            })
            enhanced = response.content or ""
        except Exception as e:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=500,
                detail=f"Enhancement failed: {str(e)}"
            )

        cursor.close()
        conn.close()
        return {
            "section":          section_title,
            "enhanced_content": enhanced
        }

    else:
        cursor.execute(
            """
            SELECT section_title, section_content
            FROM document_sections
            WHERE document_id=%s
            ORDER BY section_order
            """,
            (document_id,)
        )
        sections = cursor.fetchall()
        if not sections:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document empty")

        full_text = "\n\n".join(
            [f"{s[0]}:\n{s[1]}" for s in sections]
        )
        chain = ENHANCE_DOCUMENT_PROMPT | llm

        try:
            response = chain.invoke({
                "instruction":        instruction,
                "custom_instruction": custom_instruction,
                "full_text":          full_text
            })
            enhanced = response.content or ""
        except Exception as e:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=500,
                detail=f"Enhancement failed: {str(e)}"
            )

        cursor.close()
        conn.close()
        return {"enhanced_document": enhanced}


@router.post("/save_enhanced_section")
def save_enhanced_section(data: dict):
    conn   = get_connection()
    cursor = conn.cursor()

    document_id   = data.get("document_id")
    section_order = data.get("section_order")
    content       = data.get("content")

    cursor.execute(
        """
        UPDATE document_sections
        SET section_content=%s
        WHERE document_id=%s AND section_order=%s
        """,
        (content, document_id, section_order)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Section updated successfully"}