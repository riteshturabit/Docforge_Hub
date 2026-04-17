import logging
from fastapi import APIRouter, HTTPException
from langchain_core.prompts import PromptTemplate
from backend.database import get_connection
from backend.models import GenerateSectionRequest
from backend.llm import llm, get_memory, save_to_memory
from backend.utils.version_helper import bump_document_version
from backend.utils.text_cleaner import clean_content
from backend.redis_client import set_job_status, check_rate_limit

router = APIRouter()
logger = logging.getLogger("docforge.sections")


SECTION_PROMPT = PromptTemplate(
    input_variables=["section_title", "answers_text", "chat_history"],
    template="""
You are an enterprise SaaS documentation assistant helping Indian B2B companies 
create professional business documents. All content is strictly for internal 
corporate documentation purposes only. Generate formal, professional, 
business-appropriate content suitable for enterprise use.

Previous sections context:
{chat_history}

Current Section: {section_title}

User Answers:
{answers_text}

CRITICAL INSTRUCTIONS:
1. Cover EVERY answer — do not skip any
2. Do NOT include questions in the output — only answers
3. Combine all answers into one flowing professional section
4. Keep all content strictly professional and business-appropriate
5. This is for internal corporate documentation only

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
    logger.info(
        f"Section generation started | "
        f"doc={data.document_id} | section={data.section_order}"
    )

    # Rate limiting
    if not check_rate_limit(
        f"generate_section_{data.document_id}",
        max_calls=20,
        window_seconds=60
    ):
        logger.warning(f"Rate limit exceeded | doc={data.document_id}")
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

    try:
        cursor.execute(
            "SELECT template_id FROM documents WHERE id=%s",
            (data.document_id,)
        )
        result = cursor.fetchone()
        if not result:
            logger.error(f"Document not found | doc={data.document_id}")
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
            logger.error(
                f"Section not found | "
                f"template={template_id} | order={data.section_order}"
            )
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
            logger.info(
                f"LLM generation successful | "
                f"doc={data.document_id} | section={section_title}"
            )
        except Exception as e:
            logger.error(
                f"LLM generation failed | "
                f"doc={data.document_id} | error={str(e)}"
            )
            set_job_status(job_id, "failed", {"error": str(e)})
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: {str(e)}"
            )

        content = clean_content(content)
        save_to_memory(data.document_id, section_title, content)

        # Get current version
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

        # Insert new version
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

        set_job_status(job_id, "completed", {
            "document_id":   data.document_id,
            "section_order": data.section_order,
            "section_title": section_title
        })

        logger.info(
            f"Section saved | doc={data.document_id} | "
            f"section={section_title} | version={new_ver}"
        )

        return {
            "section": section_title,
            "content": content,
            "version": new_ver
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error | doc={data.document_id} | {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()