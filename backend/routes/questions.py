import json
import re
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.llm import llm
from backend.redis_client import check_rate_limit, is_duplicate, set_job_status

router = APIRouter()

QUESTIONS_PROMPT = PromptTemplate(
    input_variables=["template_name", "sections"],
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
- Questions must be specific and professional

Return ONLY this exact JSON format, nothing else:
{{
  "sections": [
    {{
      "section": "Overview",
      "questions": ["question 1", "question 2"]
    }}
  ]
}}

Only return JSON. No explanations. No markdown.
"""
)


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    try:
        clean = re.sub(r'```(?:json)?', '', text).strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    raise ValueError("Could not extract valid JSON from LLM response")


@router.post("/generate_questions")
def generate_questions(template_id: int):
    
    # ── Rate limiting — max 10 generations per minute ────
    if not check_rate_limit(f"generate_questions", max_calls=10, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before generating again."
        )

    #  Deduplication — prevent double generation
    dedup_key = f"questions_{template_id}"
    if is_duplicate(dedup_key, ttl=30):
        raise HTTPException(
            status_code=409,
            detail="Questions are already being generated for this template."
        )

    # Job tracking 
    job_id = f"questions_{template_id}"
    set_job_status(job_id, "processing", {"template_id": template_id})

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM document_templates WHERE id=%s",
        (template_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    template_name = result[0]

    cursor.execute(
        """
        SELECT section_title, section_order
        FROM template_sections
        WHERE template_id=%s
        ORDER BY section_order
        """,
        (template_id,)
    )
    sections      = cursor.fetchall()
    sections_text = "\n".join(
        [f"{order}. {title}" for title, order in sections]
    )

    chain = QUESTIONS_PROMPT | llm

    max_retries = 3
    data        = None

    for attempt in range(max_retries):
        try:
            response = chain.invoke({
                "template_name": template_name,
                "sections":      sections_text
            })
            data = extract_json(response.content)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM failed after {max_retries} attempts: {str(e)}"
                )
            continue

    if not data or "sections" not in data:
        raise HTTPException(status_code=500, detail="Invalid response from LLM")

    cursor.execute(
        "DELETE FROM template_questions WHERE template_id=%s",
        (template_id,)
    )

    inserted = 0
    for sec in data["sections"]:
        section_title = sec["section"]

        cursor.execute(
            """
            SELECT section_order FROM template_sections
            WHERE template_id=%s AND LOWER(section_title)=LOWER(%s)
            """,
            (template_id, section_title)
        )
        result = cursor.fetchone()

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

        for i, q in enumerate(sec["questions"], start=1):
            cursor.execute(
                """
                INSERT INTO template_questions
                (template_id, section_title, question,
                section_order, question_order)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (template_id, section_title, q, section_order, i)
            )
            inserted += 1

    conn.commit()
    cursor.close()
    conn.close()

    set_job_status(job_id, "completed", {
        "template_id":     template_id,
        "total_questions": inserted
    })

    return {
        "message":         "Questions generated and stored",
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
        "section":   section[0] if section else "",
        "questions": questions
    }


