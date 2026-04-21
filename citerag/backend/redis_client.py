import os
import json
import redis
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("citerag.redis")

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)


def cache_set(key: str, value: dict, ttl: int = 3600):
    try:
        r.setex(key, ttl, json.dumps(value))
        logger.debug(f"Cache SET | key={key}")
    except Exception as e:
        logger.error(f"Cache SET failed | {e}")


def cache_get(key: str):
    try:
        val = r.get(key)
        if val:
            logger.debug(f"Cache HIT | key={key}")
            return json.loads(val)
        return None
    except Exception as e:
        logger.error(f"Cache GET failed | {e}")
        return None


def cache_delete(key: str):
    try:
        r.delete(key)
        logger.debug(f"Cache DELETE | key={key}")
    except Exception as e:
        logger.error(f"Cache DELETE failed | {e}")


def check_rate_limit(key: str,
                     max_calls: int = 20,
                     window: int = 60) -> bool:
    try:
        current = r.incr(f"citerag:rate:{key}")
        if current == 1:
            r.expire(f"citerag:rate:{key}", window)
        return current <= max_calls
    except Exception as e:
        logger.error(f"Rate limit failed | {e}")
        return True


def cache_session(session_id: str,
                  data: dict,
                  ttl: int = 7200):
    cache_set(f"citerag:session:{session_id}", data, ttl)


def get_session(session_id: str):
    return cache_get(f"citerag:session:{session_id}")