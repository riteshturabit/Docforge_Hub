import re
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.models import GenerateSectionRequest
from backend.llm import llm, get_memory, save_to_memory
from backend.routes.versioning import bump_document_version
from backend.redis_client import set_job_status, check_rate_limit

router = APIRouter()


def clean_content(text: str) -> str:
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(?!\*)\s+', '• ', text, flags=re.MULTILINE)
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
    text = re.sub(r'^\s*[*]\s+', '• ', text, flags=re.MULTILINE)
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

CRITICAL INSTRUCTIONS:
1. Cover EVERY answer — do not skip any
2. Do NOT include questions in the output — only answers
3. Combine all answers into one flowing professional section

CRITICAL FORMATTING RULES:
1. DETECT the format of each user answer and match it exactly:
   - If user wrote bullet points, generate using • symbol
   - If user wrote a table format, generate a proper pipe table
   - If user wrote long paragraphs, split into chunks of 4 lines each

2. For bullet points:
   - If bullet has a label before colon like "Label: description" make the label BOLD
   - Format: • **Label:** description text here
   - If no label just use: • description text here
   - Keep the full content as user wrote — do not shorten

3. For tables use proper pipe format:
   | Column 1 | Column 2 | Column 3 |
   | Value 1  | Value 2  | Value 3  |

4. For long paragraphs:
   - Split into chunks of maximum 4 lines each
   - Add blank line between each chunk
   - Do not cut sentences in middle

5. AUTOMATIC BOLD AND UNDERLINE RULES — apply intelligently:
   - Make BOLD using ** **: key terms, technical names, product names,
     important concepts, policy names, role names, deadlines, numbers
     that matter, feature names, law names
   - Make UNDERLINE using __text__: critical warnings, must-do actions,
     legal requirements, zero-tolerance statements, mandatory items
   - Examples:
     • **DocForge Hub** launches **MCP Integration** in __Q2 2026__
     • __All employees must__ complete **PoSH Training** within __7 days__
     • **Self-Healing Agents** solve the **Documentation Drift** problem
   - Do NOT bold or underline every word — only what is genuinely important
   - Maximum 2-3 bold/underline items per bullet point

6. Do NOT add questions or headings in output
7. Do NOT add ## markdown
8. Keep content professional and enterprise-grade

Generate complete section covering ALL answers in user format:
"""
)


@router.post("/generate_section")
def generate_section(data: GenerateSectionRequest):

    # Rate limiting
    if not check_rate_limit(
        f"generate_section_{data.document_id}",
        max_calls=20,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before generating again."
        )

    # Job tracking
    job_id = f"section_{data.document_id}_{data.section_order}"
    set_job_status(job_id, "processing", {
        "document_id":   data.document_id,
        "section_order": data.section_order
    })

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

    #  Get current version 
    cursor.execute(
        "SELECT current_version FROM documents WHERE id=%s",
        (data.document_id,)
    )
    ver_row     = cursor.fetchone()
    current_ver = ver_row[0] if ver_row and ver_row[0] else "v1.0"

    # Check if section already exists 
    cursor.execute(
        """
        SELECT COUNT(*) FROM document_sections
        WHERE document_id=%s AND section_order=%s
        """,
        (data.document_id, data.section_order)
    )
    exists = cursor.fetchone()[0]

    if exists:
        new_ver = bump_document_version(data.document_id)
    else:
        new_ver = current_ver

    # Mark old versions as not latest 
    cursor.execute(
        """
        UPDATE document_sections
        SET is_latest = FALSE
        WHERE document_id=%s AND section_order=%s
        """,
        (data.document_id, data.section_order)
    )

    #  Insert new version 
    cursor.execute(
        """
        INSERT INTO document_sections
        (document_id, section_title, section_content,
         section_order, version, is_latest, is_completed)
        VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
        """,
        (
            data.document_id,
            section_title,
            content,
            data.section_order,
            new_ver
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    set_job_status(job_id, "completed", {
        "document_id":   data.document_id,
        "section_order": data.section_order,
        "section_title": section_title
    })

    return {
        "section": section_title,
        "content": content,
        "version": new_ver
    }