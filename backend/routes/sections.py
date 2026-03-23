from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.models import GenerateSectionRequest
from backend.llm import llm
import re

router = APIRouter()


def clean_content(text: str) -> str:
    # Remove markdown headings
    text = re.sub(r'#{1,6}\s*', '', text)
    # Remove bold/italic asterisks
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # Remove underscore bold/italic
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    # Remove markdown table separators like |---|---|
    text = re.sub(r'\|[-:\s|]+\|', '', text)
    # Clean table rows — keep content, remove pipes
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            # It's a table row — extract cell content
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            cells = [c for c in cells if c]
            cleaned_lines.append('  |  '.join(cells))
        else:
            cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    # Remove bullet points
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # Remove extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


@router.post("/generate_section")
def generate_section(data: GenerateSectionRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT template_id FROM documents WHERE id=%s",
        (data.document_id,)
    )
    template_id = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT section_title FROM template_sections
        WHERE template_id=%s AND section_order=%s
        """,
        (template_id, data.section_order)
    )
    section_title = cursor.fetchone()[0]

    answers_text = "\n".join(
        [f"{a.question}: {a.answer}" for a in data.answers]
    )

    prompt = f"""
You are an enterprise SaaS documentation assistant.
Generate professional content for the following section.

Section: {section_title}

User Answers:
{answers_text}

Guidelines:
- Keep it professional
- Strictly use the user's answers
- Expand only for clarity and professionalism
- Do not add assumptions or new policies
- Do not use ## headings or **bold** or __underline__ markdown
- Do not use markdown formatting like ##, **, __, or bullet symbols
- If using a table use proper pipe format like | Col1 | Col2 |
- Write in clean plain paragraphs only
- Table must have a header row followed by a separator row like |---|---|
"""

    response = llm.invoke(prompt)
    content = clean_content(response.content or "No content generated")

    cursor.execute(
        """
        DELETE FROM document_sections
        WHERE document_id=%s AND section_order=%s
        """,
        (data.document_id, data.section_order)
    )

    cursor.execute(
        """
        INSERT INTO document_sections
        (document_id, section_title, section_content, section_order, is_completed)
        VALUES (%s,%s,%s,%s,TRUE)
        """,
        (data.document_id, section_title, content, data.section_order)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {"section": section_title, "content": content}
