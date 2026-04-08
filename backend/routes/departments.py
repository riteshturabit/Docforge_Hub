import logging
from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.redis_client import cache_get, cache_set

router = APIRouter()
logger = logging.getLogger("docforge.departments")

@router.get("/departments")
def get_departments():
    cached = cache_get("departments")
    if cached:
        logger.debug("Departments cache HIT")
        return {"departments": cached}

    logger.info("Fetching departments from DB")
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM departments")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        logger.warning("No departments found in DB")
        raise HTTPException(status_code=404, detail="No departments found")

    cache_set("departments", data, ttl=3600)
    logger.info(f"Departments fetched and cached | total={len(data)}")
    return {"departments": data}