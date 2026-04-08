import logging
from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.redis_client import cache_get, cache_set

router = APIRouter()
logger = logging.getLogger("docforge.templates")

@router.get("/templates/{department_id}")
def get_templates(department_id: int):
    cache_key = f"templates_{department_id}"
    cached    = cache_get(cache_key)
    if cached:
        logger.debug(f"Templates cache HIT | dept={department_id}")
        return {"templates": cached}

    logger.info(f"Fetching templates from DB | dept={department_id}")
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM document_templates WHERE department_id=%s",
        (department_id,)
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        logger.warning(f"No templates found | dept={department_id}")
        raise HTTPException(
            status_code=404,
            detail="No templates found for this department"
        )

    cache_set(cache_key, data, ttl=3600)
    logger.info(f"Templates fetched and cached | dept={department_id} | total={len(data)}")
    return {"templates": data}


@router.get("/sections/{template_id}")
def get_sections(template_id: int):
    cache_key = f"sections_{template_id}"
    cached    = cache_get(cache_key)
    if cached:
        logger.debug(f"Sections cache HIT | template={template_id}")
        return {"sections": cached}

    logger.info(f"Fetching sections from DB | template={template_id}")
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT section_title, section_order
        FROM template_sections
        WHERE template_id=%s
        ORDER BY section_order
        """,
        (template_id,)
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        logger.warning(f"No sections found | template={template_id}")
        raise HTTPException(
            status_code=404,
            detail="No sections found for this template"
        )

    cache_set(cache_key, data, ttl=3600)
    logger.info(f"Sections fetched and cached | template={template_id} | total={len(data)}")
    return {"sections": data}