import re
import logging
from backend.database import get_connection

logger = logging.getLogger("docforge.utils.version_helper")


def get_next_version(current_version: str) -> str:
    """
    Increments the minor version number.
    v1.0 → v1.1 → v1.2 etc.
    """
    try:
        match = re.match(r'v(\d+)\.(\d+)', current_version)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return f"v{major}.{minor + 1}"
    except Exception:
        pass
    return "v1.1"


def bump_document_version(document_id: str) -> str:
    """
    Fetches current version from DB,
    increments it and saves back.
    Returns the new version string.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT current_version FROM documents WHERE id = %s",
            (document_id,)
        )
        row = cursor.fetchone()
        if not row:
            return "v1.0"

        current = row[0] or "v1.0"
        new_ver = get_next_version(current)

        cursor.execute(
            "UPDATE documents SET current_version = %s WHERE id = %s",
            (new_ver, document_id)
        )
        conn.commit()
        logger.info(
            f"Version bumped | doc={document_id} "
            f"| {current} → {new_ver}"
        )
        return new_ver

    except Exception as e:
        logger.error(f"Version bump failed | doc={document_id} | {e}")
        conn.rollback()
        return "v1.1"
    finally:
        cursor.close()
        conn.close()