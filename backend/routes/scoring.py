import json
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.llm import llm
from backend.redis_client import cache_get, cache_set

router = APIRouter()

SCORING_PROMPT = PromptTemplate(
    input_variables=["document_title", "document_type", "sections_text"],
    template="""
You are an expert enterprise document quality evaluator.

Evaluate the following document and score it on 5 parameters.
Each parameter is scored out of 20. Total score is out of 100.

Document Title: {document_title}
Document Type: {document_type}

Document Content:
{sections_text}

Scoring Parameters:
1. Completeness (0-20): Are all sections filled with meaningful content? No empty or placeholder text?
2. Professionalism (0-20): Is the language enterprise-grade, formal and polished?
3. Consistency (0-20): Do all sections align with each other in tone, terminology and context?
4. Clarity (0-20): Is the content clear, well-structured and easy to understand?
5. Relevance (0-20): Does the content match the document type, industry and purpose?

Return ONLY this exact JSON format:
{{
  "overall_score": 85,
  "completeness": 17,
  "professionalism": 18,
  "consistency": 16,
  "clarity": 17,
  "relevance": 17,
  "summary": "One sentence summary of document quality"
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
    import re
    try:
        clean = re.sub(r'```(?:json)?', '', text).strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    raise ValueError("Could not extract valid JSON from LLM response")


@router.post("/score_document/{document_id}")
def score_document(document_id: str):

    # ── Check cache first ─────────────────────────────────
    cache_key = f"score_{document_id}"
    cached    = cache_get(cache_key)
    if cached:
        return cached

    conn   = get_connection()
    cursor = conn.cursor()

    # ── Get document metadata ─────────────────────────────
    cursor.execute(
        """
        SELECT
            d.title,
            dty.name AS document_type
        FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        JOIN document_types dty ON dt.document_type_id = dty.id
        WHERE d.id = %s
        """,
        (document_id,)
    )
    meta = cursor.fetchone()
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    document_title = meta[0]
    document_type  = meta[1]

    # ── Get all sections ──────────────────────────────────
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

    if not sections:
        raise HTTPException(
            status_code=400,
            detail="No sections found. Generate document first."
        )

    # Build sections text for LLM
    sections_text = "\n\n".join([
        f"Section {s[2]} — {s[0]}:\n{s[1][:300]}..."
        if len(s[1]) > 300 else f"Section {s[2]} — {s[0]}:\n{s[1]}"
        for s in sections
    ])

    # ── Score using LangChain ─────────────────────────────
    chain = SCORING_PROMPT | llm

    try:
        response = chain.invoke({
            "document_title": document_title,
            "document_type":  document_type,
            "sections_text":  sections_text
        })
        score_data = extract_json(response.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}"
        )

    # Validate scores
    for field in ["completeness", "professionalism", "consistency", "clarity", "relevance"]:
        if field not in score_data:
            score_data[field] = 15

    # Calculate overall if not provided
    if "overall_score" not in score_data:
        score_data["overall_score"] = (
            score_data["completeness"] +
            score_data["professionalism"] +
            score_data["consistency"] +
            score_data["clarity"] +
            score_data["relevance"]
        )

    # ── Save to DB ────────────────────────────────────────
    breakdown = {
        "completeness":    score_data["completeness"],
        "professionalism": score_data["professionalism"],
        "consistency":     score_data["consistency"],
        "clarity":         score_data["clarity"],
        "relevance":       score_data["relevance"],
        "summary":         score_data.get("summary", "")
    }

    cursor.execute(
        """
        UPDATE documents
        SET quality_score=%s, score_breakdown=%s
        WHERE id=%s
        """,
        (
            score_data["overall_score"],
            json.dumps(breakdown),
            document_id
        )
    )
    conn.commit()
    cursor.close()
    conn.close()

    result = {
        "document_id":     document_id,
        "overall_score":   score_data["overall_score"],
        "breakdown":       breakdown,
        "grade":           get_grade(score_data["overall_score"])
    }

    # ── Cache for 1 hour ──────────────────────────────────
    cache_set(cache_key, result, ttl=3600)

    return result


@router.get("/score_document/{document_id}")
def get_score(document_id: str):

    # ── Check cache first ─────────────────────────────────
    cache_key = f"score_{document_id}"
    cached    = cache_get(cache_key)
    if cached:
        return cached

    # ── Fetch from DB ─────────────────────────────────────
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT quality_score, score_breakdown
        FROM documents
        WHERE id=%s
        """,
        (document_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or result[0] is None:
        return {
            "document_id":   document_id,
            "overall_score": None,
            "breakdown":     None,
            "grade":         None
        }

    score     = result[0]
    breakdown = result[1]

    response = {
        "document_id":   document_id,
        "overall_score": score,
        "breakdown":     breakdown,
        "grade":         get_grade(score)
    }

    cache_set(cache_key, response, ttl=3600)
    return response


def get_grade(score: int) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"