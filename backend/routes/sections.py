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
You are an enterprise documentation writer for Indian B2B companies.
Generate professional business document content based on the answers provided.

Previous sections context:
{chat_history}

Current Section: {section_title}

User Answers:
{answers_text}

Generation rules:

1. If user answers are provided:
   - Generate content strictly based on the user answers only
   - Do not add generic content or filler text
   - Do not add introductory labels like "Purpose:" or "Overview:" at the start
   - Generate content that directly answers each question
   - Keep content specific to the company and context mentioned in answers

2. If no answers are provided:
   - Generate professional content based on the section title
   - Use Indian B2B enterprise best practices
   - Keep content specific and actionable

3. Output format — follow this exact structure:

   For each question or topic, generate a sub-heading followed by bullet points:

   Sub-heading Title
   • **Bold Label:** Description of the point here with specific details
   • **Bold Label:** Description of the point here with specific details
   • **Bold Label:** Description of the point here with specific details
   • **Bold Label:** Description of the point here with specific details

   Rules for bullet points:
   - Minimum 4 bullet points per sub-section
   - Maximum 6 bullet points per sub-section
   - Every bullet point must have a bold label before the colon
   - Label must be 1-3 words describing the point
   - Description after colon must be specific and detailed
   - No generic filler content like "This section covers..."
   - No introductory sentences before bullet points
   - No concluding sentences after bullet points

4. For tables — if user answer has tabular data:
   | Column 1 | Column 2 | Column 3 |
   |---|---|---|
   | Value 1  | Value 2  | Value 3  |

5. Bold and underline rules:
   - Bold using ** **: key terms, names, deadlines, numbers
   - Underline using __ __: warnings, mandatory items only
   - Do not overuse — maximum 2 bold items per bullet

6. Never include:
   - The word "Purpose:" as a label at start of any bullet
   - The word "Overview:" as a label at start of any bullet
   - Questions in the output
   - Markdown headers using ##
   - Any preamble before the content
   - Any closing remarks after the content
   - Generic sentences like "This document covers..."
   - Any content not related to the user answers

Example of correct output format:

Review Process
- **RFC Submission:** Architect submits formal Request for Comments document to engineering leadership team
- **Review Period:** Minimum 5 working day review period allowing all stakeholders to provide written feedback
- **Architecture Review Board:** Dedicated ARB meeting conducted with CTO, Tech Leads and senior engineers
- **Final Approval:** CTO provides final written approval before any significant architectural changes implemented

Reviewers
- **CTO:** Reviews overall strategic alignment, scalability approach and technology stack decisions
- **Tech Leads:** Evaluate technical feasibility, implementation complexity and team capability requirements
- **Security Engineer:** Reviews all security controls, data protection measures and compliance requirements
- **DevOps Lead:** Assesses deployment strategy, infrastructure requirements and operational complexity

Generate the section content now following the exact format above:
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

        # Handle empty answers gracefully
        if data.answers and len(data.answers) > 0:
            filled_answers = [
                a for a in data.answers
                if a.answer and a.answer.strip()
            ]
            if filled_answers:
                answers_text = "\n".join(
                    [
                        f"Question: {a.question}\nAnswer: {a.answer}"
                        for a in filled_answers
                    ]
                )
            else:
                answers_text = (
                    f"No answers provided. "
                    f"Generate professional content for section: {section_title}"
                )
        else:
            answers_text = (
                f"No answers provided. "
                f"Generate professional content for section: {section_title}"
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