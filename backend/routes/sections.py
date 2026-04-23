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
Generate professional business document content strictly based on the answers provided.

Previous sections context:
{chat_history}

Current Section: {section_title}

User Answers:
{answers_text}

Generation rules:

1. Process each question and answer one by one separately
2. For each question:
   - Extract 1 to 3 key words from the question that best describe the topic
   - Use those key words as a bold sub-heading title for that answer
   - Generate 2 to 3 bullet points for that answer only
   - Each bullet point should be 2 to 3 lines long
   - Content must be strictly based on the user answer provided
   - Do not add random content not mentioned in the answer
   - Do not mix content from different questions

3. If no answer is provided for a question:
   - Still generate the bold sub-heading from question keywords
   - Generate 2 to 3 relevant professional bullet points based on the question

4. Output format for each question:

**Sub-heading Title From Question Keywords**
- **Bold Label:** Detailed description here spanning 2 to 3 lines covering
  the specific point mentioned in the user answer with relevant context
  and professional language appropriate for enterprise documentation
- **Bold Label:** Another specific point from the answer with 2 to 3 lines
  of professional content directly related to what the user answered
- **Bold Label:** Third point if needed based on answer depth and content
  requirements of the question asked

5. Bullet point rules:
   - Every bullet must start with a bold label of 1 to 3 words
   - Label must be extracted from the answer content itself
   - Description after colon must be 2 to 3 lines long
   - Content must be strictly from user answer — no random additions
   - Do not repeat same point in different bullets

6. Sub-heading rules:
   - Extract the core topic words from the question
   - Example: "What is the review process?" → **Review Process**
   - Example: "Who are the reviewers?" → **Reviewers**
   - Example: "How is feedback tracked?" → **Feedback Tracking**
   - Sub-heading must be bold using ** **
   - No colon after sub-heading
   - One blank line before each sub-heading

7. Never include:
   - The words "Purpose:" or "Overview:" as bullet labels
   - Generic filler content not from user answers
   - Questions in the output
   - Markdown headers using ## or #
   - Any preamble or introduction before content
   - Any conclusion or summary after content
   - More than 3 bullets per question
   - More than 3 lines per bullet point

Example of correct output:

**Review Process**
- **RFC Submission:** Architect submits formal Request for Comments
  document to engineering leadership team for structured review
  before any significant architectural changes are implemented
- **Review Period:** Minimum 5 working day review period allowing all
  stakeholders to provide written feedback on the proposed changes
  ensuring comprehensive evaluation before final decision

**Reviewers**
- **CTO:** Reviews overall strategic alignment, scalability approach
  and technology stack decisions ensuring alignment with company
  vision and long term technical roadmap
- **Tech Leads:** Evaluate technical feasibility, implementation
  complexity and team capability requirements for proposed changes
  providing detailed feedback from engineering perspective

**Feedback Tracking**
- **GitHub Discussions:** All architecture feedback recorded as GitHub
  discussions on RFC pull request maintaining full audit trail
  of all comments and decisions made during review process
- **Decision Log:** Significant decisions and rejected alternatives
  documented in Architecture Decision Records for future reference
  and organizational knowledge preservation

Generate the section content now following exact format above:
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

        # Build answers text question by question
        if data.answers and len(data.answers) > 0:
            qa_parts = []
            for i, a in enumerate(data.answers, 1):
                answer_text = a.answer.strip() if a.answer else ""
                if answer_text:
                    qa_parts.append(
                        f"Question {i}: {a.question}\n"
                        f"Answer {i}: {answer_text}"
                    )
                else:
                    qa_parts.append(
                        f"Question {i}: {a.question}\n"
                        f"Answer {i}: No answer provided"
                    )
            answers_text = "\n\n".join(qa_parts)
        else:
            answers_text = (
                f"No answers provided. "
                f"Generate professional content for: {section_title}"
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