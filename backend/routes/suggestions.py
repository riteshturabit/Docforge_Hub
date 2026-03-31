import json
import re
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.llm import llm
from backend.redis_client import cache_get, cache_set

router = APIRouter()

SUGGESTIONS_PROMPT = PromptTemplate(
    input_variables=["user_input", "templates_list"],
    template="""
You are an expert enterprise document consultant.

A company has described their needs. Based on their description,
suggest the TOP 5 most relevant document templates from the available list.

Company Description:
{user_input}

Available Templates:
{templates_list}

Rules:
- Select exactly 5 templates that best match the company's needs
- Consider their industry, stage, department needs and goals
- Give a specific reason why each template is relevant to them
- Reason should be 1 sentence, specific to their description

Return ONLY this exact JSON format:
{{
  "suggestions": [
    {{
      "template_id": 1,
      "template_name": "Employee Handbook",
      "department": "HR",
      "document_type": "Policy",
      "relevance_reason": "Essential for Series A startups to establish company culture and employee expectations."
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


@router.post("/suggest_templates")
def suggest_templates(data: dict):

    user_input = data.get("user_input", "").strip()

    if not user_input:
        raise HTTPException(
            status_code=400,
            detail="Please describe your company and document needs."
        )

    if len(user_input) < 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide more details about your company."
        )

    #  Check cache 
    import hashlib
    cache_key = f"suggestions_{hashlib.md5(user_input.encode()).hexdigest()}"
    cached    = cache_get(cache_key)
    if cached:
        return cached

    # Get all templates from DB 
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            dt.id,
            dt.name,
            dep.name AS department,
            dty.name AS document_type,
            dt.industry
        FROM document_templates dt
        JOIN departments dep ON dt.department_id = dep.id
        JOIN document_types dty ON dt.document_type_id = dty.id
        ORDER BY dt.id
        """
    )
    templates = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build templates list for LLM
    templates_text = "\n".join([
        f"ID:{t[0]} | {t[1]} | Department:{t[2]} | Type:{t[3]}"
        for t in templates
    ])

    # LangChain call 
    chain = SUGGESTIONS_PROMPT | llm

    try:
        response = chain.invoke({
            "user_input":     user_input,
            "templates_list": templates_text
        })
        data_parsed = extract_json(response.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion failed: {str(e)}"
        )

    if "suggestions" not in data_parsed:
        raise HTTPException(
            status_code=500,
            detail="Invalid response from LLM"
        )

    # Build response 
    # Get template_id to department_id mapping for frontend navigation
    conn   = get_connection()
    cursor = conn.cursor()

    enriched = []
    for s in data_parsed["suggestions"][:5]:
        tid = s.get("template_id")
        cursor.execute(
            """
            SELECT dt.id, dt.name, dep.id, dep.name, dty.name
            FROM document_templates dt
            JOIN departments dep ON dt.department_id = dep.id
            JOIN document_types dty ON dt.document_type_id = dty.id
            WHERE dt.id = %s
            """,
            (tid,)
        )
        row = cursor.fetchone()
        if row:
            enriched.append({
                "template_id":      row[0],
                "template_name":    row[1],
                "department_id":    row[2],
                "department":       row[3],
                "document_type":    row[4],
                "relevance_reason": s.get("relevance_reason", "")
            })

    cursor.close()
    conn.close()

    result = {
        "user_input":   user_input,
        "suggestions":  enriched,
        "total":        len(enriched)
    }

    # Cache for 30 mins 
    cache_set(cache_key, result, ttl=1800)

    return result