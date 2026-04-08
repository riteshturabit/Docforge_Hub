import logging
import psycopg2

logger = logging.getLogger("docforge.database")

def get_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="DocForge_Hub",
            user="postgres",
            password="postgres123",
            port="5432"
        )
        logger.debug("DB connection established")
        return conn
    except Exception as e:
        logger.error(f"DB connection failed: {str(e)}")
        raise