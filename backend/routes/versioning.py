import re
from fastapi import APIRouter, HTTPException
from backend.database import get_connection

router = APIRouter()


def get_next_version(current_version: str) -> str:
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
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT current_version FROM documents WHERE id = %s",
        (document_id,)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return "v1.0"

    current = row[0] or "v1.0"
    new_ver = get_next_version(current)

    cursor.execute(
        "UPDATE documents SET current_version = %s WHERE id = %s",
        (new_ver, document_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return new_ver


def save_section_version(
    document_id: str,
    section_order: int,
    section_title: str,
    content: str,
    version: str
):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE document_sections
        SET is_latest = FALSE
        WHERE document_id = %s AND section_order = %s
        """,
        (document_id, section_order)
    )

    cursor.execute(
        """
        INSERT INTO document_sections
            (document_id, section_title, section_content,
             section_order, version, is_latest, created_at)
        VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
        """,
        (document_id, section_title, content, section_order, version)
    )
    conn.commit()
    cursor.close()
    conn.close()


@router.get("/versions/{document_id}/{section_order}")
def get_section_versions(document_id: str, section_order: int):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id, section_title, section_content,
            version, is_latest, created_at
        FROM document_sections
        WHERE document_id = %s AND section_order = %s
        ORDER BY created_at DESC
        """,
        (document_id, section_order)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return {
            "document_id":   document_id,
            "section_order": section_order,
            "versions":      []
        }

    versions = []
    for row in rows:
        versions.append({
            "id":            str(row[0]),
            "section_title": row[1],
            "content":       row[2],
            "version":       row[3] or "v1.0",
            "is_latest":     row[4],
            "created_at":    row[5].strftime("%B %d, %Y %H:%M") if row[5] else ""
        })

    return {
        "document_id":   document_id,
        "section_order": section_order,
        "versions":      versions
    }


@router.post("/versions/restore/{document_id}/{section_order}/{section_id}")
def restore_version(document_id: str, section_order: int, section_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT section_title, section_content, version
        FROM document_sections
        WHERE id = %s AND document_id = %s
        """,
        (section_id, document_id)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Version not found")

    sec_title   = row[0]
    sec_content = row[1]

    new_ver = bump_document_version(document_id)

    cursor.execute(
        """
        UPDATE document_sections
        SET is_latest = FALSE
        WHERE document_id = %s AND section_order = %s
        """,
        (document_id, section_order)
    )

    cursor.execute(
        """
        INSERT INTO document_sections
            (document_id, section_title, section_content,
             section_order, version, is_latest, created_at)
        VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
        """,
        (document_id, sec_title, sec_content, section_order, new_ver)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "message":       "Version restored successfully",
        "new_version":   new_ver,
        "section_order": section_order
    }


@router.get("/versions/document/{document_id}")
def get_document_version(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT current_version FROM documents WHERE id = %s",
        (document_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id":     document_id,
        "current_version": row[0] or "v1.0"
    }