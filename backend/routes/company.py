import logging
from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.models import CompanyContext

router = APIRouter()
logger = logging.getLogger("docforge.company")

@router.post("/company-context")
def save_company_context(data: CompanyContext):
    logger.info(f"Saving company context | name={data.company_name}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO company_context
        (company_name, company_location, company_size,
        company_stage, product_type, target_customers,
        company_mission, company_vision)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            data.company_name,
            data.company_location,
            data.company_size,
            data.company_stage,
            data.product_type,
            data.target_customers,
            data.company_mission,
            data.company_vision
        )
    )
    company_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    logger.info(f"Company context saved | company_id={company_id} | name={data.company_name}")
    return {"company_id": company_id}


@router.get("/company-context/{company_id}")
def get_company_context(company_id: int):
    logger.info(f"Fetching company context | company_id={company_id}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, company_name, company_location,
               company_size, company_stage, product_type,
               target_customers, company_mission,
               company_vision, created_at
        FROM company_context
        WHERE id=%s
        """,
        (company_id,)
    )
    result = cursor.fetchone()
    if not result:
        logger.error(f"Company context not found | company_id={company_id}")
        raise HTTPException(status_code=404, detail="Company context not found")
    cursor.close()
    conn.close()

    logger.info(f"Company context fetched | company_id={company_id}")
    return {
        "id": result[0],
        "company_name": result[1],
        "company_location": result[2],
        "company_size": result[3],
        "company_stage": result[4],
        "product_type": result[5],
        "target_customers": result[6],
        "company_mission": result[7],
        "company_vision": result[8],
        "created_at": str(result[9])
    }