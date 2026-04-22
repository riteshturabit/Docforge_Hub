import os
import json
import hashlib
import redis
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("statecase.redis")

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)


def cache_state(session_id: str, state: dict, ttl: int = 7200):
    """Cache full session state"""
    try:
        r.setex(
            f"sc:state:{session_id}",
            ttl,
            json.dumps(state)
        )
        logger.debug(f"State cached | session={session_id}")
    except Exception as e:
        logger.error(f"State cache failed | {e}")


def get_state(session_id: str) -> dict:
    """Get cached session state"""
    try:
        val = r.get(f"sc:state:{session_id}")
        return json.loads(val) if val else {}
    except Exception as e:
        logger.error(f"State get failed | {e}")
        return {}


def cache_messages(session_id: str,
                   messages: list,
                   ttl: int = 7200):
    """Cache message history"""
    try:
        r.setex(
            f"sc:messages:{session_id}",
            ttl,
            json.dumps(messages)
        )
    except Exception as e:
        logger.error(f"Messages cache failed | {e}")


def get_messages(session_id: str) -> list:
    """Get cached message history"""
    try:
        val = r.get(f"sc:messages:{session_id}")
        return json.loads(val) if val else []
    except Exception as e:
        logger.error(f"Messages get failed | {e}")
        return []


def check_rate_limit(key: str,
                     max_calls: int = 30,
                     window: int = 60) -> bool:
    """Rate limit check"""
    try:
        current = r.incr(f"sc:rate:{key}")
        if current == 1:
            r.expire(f"sc:rate:{key}", window)
        return current <= max_calls
    except Exception as e:
        logger.error(f"Rate limit failed | {e}")
        return True


def set_ticket_lock(question: str, ttl: int = 300) -> bool:
    """
    Prevent duplicate ticket creation using NX lock.
    Hashes question text to create unique key.
    Returns True if lock acquired (first time)
    Returns False if lock exists (duplicate!)
    """
    try:
        ticket_hash = hashlib.md5(
            question.encode()
        ).hexdigest()
        result = r.set(
            f"sc:ticket_lock:{ticket_hash}",
            "1",
            nx=True,
            ex=ttl
        )
        return result is not None
    except Exception as e:
        logger.error(f"Ticket lock failed | {e}")
        return True