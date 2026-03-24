import json
from fastapi import APIRouter, HTTPException
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from backend.database import get_connection
from backend.llm import llm

router = APIRouter()


# ── Pydantic schema for LLM output ───────────────────────
class SectionQuestions(BaseModel):
    section: str = Field(description="Section title")
    questions: List[str] = Field(description="List of questions for this section")

class DocumentQuestions(BaseModel):
    sections: List[SectionQuestions] = Field(
        description="List of sections with questions"
    )


# ── Prompt template ───────────────────────────────────────
QUESTIONS_PROMPT = PromptTemplate(
    input_variables=["template_name", "sections", "format_instructions"],
    template="""
You are an enterprise SaaS documentation assistant.

Generate 40-45 questions required to create the following document.

Document: {template_name}

Sections:
{sections}

Rules:
- Generate 2-3 questions PER section
- Map each question to its exact section title
- Total questions should be 40-45
- Questions must be specific and help generate professional content

{format_instructions}
"""
)


@router.post("/generate_questions")
def generate_questions(template_id: int):
    conn   = get_connection()
    cursor = conn.cursor()

    # Get template name
    cursor.execute(
        "SELECT name FROM document_templates WHERE id=%s",
        (template_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    template_name = result[0]

    # Get sections
    cursor.execute(
        """
        SELECT section_title, section_order
        FROM template_sections
        WHERE template_id=%s
        ORDER BY section_order
        """,
        (template_id,)
    )
    sections = cursor.fetchall()
    sections_text = "\n".join(
        [f"{order}. {title}" for title, order in sections]
    )

    # ── Use PydanticOutputParser ──────────────────────────
    parser = PydanticOutputParser(pydantic_object=DocumentQuestions)

    prompt = QUESTIONS_PROMPT.format(
        template_name=template_name,
        sections=sections_text,
        format_instructions=parser.get_format_instructions()
    )

    # ── Invoke with retry ─────────────────────────────────
    try:
        response = llm.invoke(prompt)
        data     = parser.parse(response.content)
    except Exception:
        # Fallback to raw JSON parsing
        try:
            raw = response.content
            # Extract JSON from response
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end != 0:
                data = DocumentQuestions.parse_raw(raw[start:end])
            else:
                raise HTTPException(
                    status_code=500,
                    detail="LLM returned invalid format. Try again."
                )
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to parse questions. Try again."
            )

    # Delete old questions
    cursor.execute(
        "DELETE FROM template_questions WHERE template_id=%s",
        (template_id,)
    )

    # Insert new questions
    inserted = 0
    for sec in data.sections:
        section_title = sec.section

        # Exact match
        cursor.execute(
            """
            SELECT section_order FROM template_sections
            WHERE template_id=%s AND LOWER(section_title)=LOWER(%s)
            """,
            (template_id, section_title)
        )
        result = cursor.fetchone()

        # Fuzzy match if not found
        if not result:
            cursor.execute(
                """
                SELECT section_order FROM template_sections
                WHERE template_id=%s AND LOWER(section_title) LIKE LOWER(%s)
                """,
                (template_id, f"%{section_title}%")
            )
            result = cursor.fetchone()

        if not result:
            continue

        section_order = result[0]

        for i, q in enumerate(sec.questions, start=1):
            cursor.execute(
                """
                INSERT INTO template_questions
                (template_id, section_title, question, section_order, question_order)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (template_id, section_title, q, section_order, i)
            )
            inserted += 1

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "message": "Questions generated and stored",
        "total_questions": inserted
    }


@router.get("/next_questions")
def get_next_questions(document_id: str, section_order: int):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT template_id FROM documents WHERE id=%s",
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    template_id = result[0]

    cursor.execute(
        """
        SELECT question FROM template_questions
        WHERE template_id=%s AND section_order=%s
        ORDER BY question_order
        """,
        (template_id, section_order)
    )
    questions = [row[0] for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT section_title FROM template_sections
        WHERE template_id=%s AND section_order=%s
        """,
        (template_id, section_order)
    )
    section = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "section": section[0] if section else "",
        "questions": questions
    }