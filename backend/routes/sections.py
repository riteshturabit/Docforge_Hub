import re
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.models import GenerateSectionRequest
from backend.llm import llm, get_memory, save_to_memory

router = APIRouter()


def clean_content(text: str) -> str:
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    text = re.sub(r'\|[-:\s|]+\|', '', text)
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            cells = [c for c in cells if c]
            cleaned.append('  |  '.join(cells))
        else:
            cleaned.append(line)
    text = '\n'.join(cleaned)
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


SECTION_PROMPT = PromptTemplate(
    input_variables=["section_title", "answers_text", "chat_history"],
    template="""
You are an enterprise SaaS documentation assistant.
Generate professional content for the following document section.

Previous sections context:
{chat_history}

Current Section: {section_title}

User Answers:
{answers_text}

Guidelines:
- Keep it professional and enterprise-grade
- Strictly use the user answers as the basis
- Expand only for clarity and professionalism
- Be consistent with previously generated sections
- Do not add assumptions or new policies
- Do not use markdown formatting like ##, **, __ or bullet symbols
- Write in clean plain paragraphs only
- If using a table use proper pipe format like | Col1 | Col2 |

Generate the section content now:
"""
)


@router.post("/generate_section")
def generate_section(data: GenerateSectionRequest):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT template_id FROM documents WHERE id=%s",
        (data.document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    template_id = result[0]

    cursor.execute(
        """
        SELECT section_title FROM template_sections
        WHERE template_id=%s AND section_order=%s
        """,
        (template_id, data.section_order)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Section not found")
    section_title = result[0]

    answers_text = "\n".join(
        [f"{a.question}: {a.answer}" for a in data.answers]
    )

    memory       = get_memory(data.document_id)
    chat_history = ""
    messages     = memory.messages
    if messages:
        recent_messages = messages[-4:]
        chat_history    = "\n".join([m.content for m in recent_messages])

    chain = SECTION_PROMPT | llm

    try:
        response = chain.invoke({
            "section_title": section_title,
            "answers_text":  answers_text,
            "chat_history":  chat_history or "No previous sections yet."
        })
        content = response.content or "No content generated"
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM generation failed: {str(e)}"
        )

    content = clean_content(content)

    save_to_memory(data.document_id, section_title, content)

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
        (document_id, section_title, section_content,
        section_order, is_completed)
        VALUES (%s,%s,%s,%s,TRUE)
        """,
        (data.document_id, section_title, content, data.section_order)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {"section": section_title, "content": content}