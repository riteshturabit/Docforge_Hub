import os
import logging
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()  # ← THIS WAS MISSING!

logger = logging.getLogger("shared.database")

# Connection pool shared across citerag and statecase
_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=2,
            maxconn=20,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME", "DocForge_Hub"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres123")
        )
        logger.info("Database connection pool created")
    return _pool


def get_connection():
    try:
        conn = get_pool().getconn()
        return conn
    except Exception as e:
        logger.error(f"DB connection failed | {e}")
        raise


def release_connection(conn):
    try:
        get_pool().putconn(conn)
    except Exception as e:
        logger.error(f"DB release failed | {e}")