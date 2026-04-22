import logging
from statecase.backend.database import get_connection, release_connection
from statecase.backend.redis_client import (
    cache_state, get_state,
    cache_messages, get_messages
)

logger = logging.getLogger("statecase.memory")


def load_session(session_id: str) -> dict:
    """
    Load session state.
    Try Redis first (fast) → fallback to PostgreSQL (durable)
    """
    # Try Redis first
    state = get_state(session_id)
    if state:
        logger.debug(f"Session from Redis | session={session_id}")
        return state

    # Fallback to PostgreSQL
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_industry, current_intent,
                   state, last_retrieved
            FROM sc_sessions
            WHERE session_id=%s
            """,
            (session_id,)
        )
        row = cursor.fetchone()

        if row:
            state = {
                "session_id":     session_id,
                "user_industry":  row[0] or "General",
                "current_intent": row[1],
                "state":          row[2] or "idle",
                "last_retrieved": row[3],
            }
            # Re-cache in Redis
            cache_state(session_id, state)
            logger.info(f"Session from DB | session={session_id}")
            return state

        # Brand new session
        logger.info(f"New session | session={session_id}")
        return {
            "session_id":     session_id,
            "user_industry":  "General",
            "current_intent": None,
            "state":          "idle",
            "last_retrieved": None,
        }

    except Exception as e:
        logger.error(f"Load session failed | {e}")
        return {"session_id": session_id, "state": "idle"}
    finally:
        cursor.close()
        release_connection(conn)


def save_session(session_id: str, state: dict):
    """
    Save session to both Redis and PostgreSQL
    Upsert pattern — insert or update
    """
    # Save to Redis
    cache_state(session_id, state)

    # Save to PostgreSQL
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO sc_sessions
            (session_id, user_industry, current_intent,
             state, last_retrieved, updated_at)
            VALUES (%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (session_id) DO UPDATE SET
                user_industry  = EXCLUDED.user_industry,
                current_intent = EXCLUDED.current_intent,
                state          = EXCLUDED.state,
                last_retrieved = EXCLUDED.last_retrieved,
                updated_at     = NOW()
            """,
            (
                session_id,
                state.get("user_industry", "General"),
                state.get("current_intent"),
                state.get("state", "idle"),
                str(state.get("last_retrieved", ""))
            )
        )
        conn.commit()
        logger.debug(f"Session saved | session={session_id}")
    except Exception as e:
        logger.error(f"Save session failed | {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def load_messages(session_id: str) -> list:
    """
    Load message history.
    Try Redis first → fallback to PostgreSQL
    """
    # Try Redis
    messages = get_messages(session_id)
    if messages:
        return messages

    # Fallback to PostgreSQL
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT role, content
            FROM sc_messages
            WHERE session_id=%s
            ORDER BY created_at ASC
            LIMIT 20
            """,
            (session_id,)
        )
        rows     = cursor.fetchall()
        messages = [{"role": r[0], "content": r[1]} for r in rows]
        cache_messages(session_id, messages)
        return messages
    except Exception as e:
        logger.error(f"Load messages failed | {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def save_message(session_id: str, role: str, content: str):
    """Save single message to PostgreSQL"""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO sc_messages (session_id, role, content)
            VALUES (%s,%s,%s)
            """,
            (session_id, role, content)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Save message failed | {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)