import redis
import json
from datetime import datetime, date
from dotenv import load_dotenv
import os

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

def get_redis():
    return redis_client


# Custom JSON serializer 
class CustomEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, tuple):
            return list(o)
        return super().default(o)

def to_json(data: object) -> str:
    return json.dumps(data, cls=CustomEncoder)

def from_json(data: str) -> object:
    return json.loads(data)


# JOB TRACKING

def set_job_status(job_id: str, status: str, meta: dict[str, object] = {}) -> None:
    data: dict[str, object] = {"status": status, **meta}
    redis_client.setex(
        f"job:{job_id}",
        3600,
        to_json(data)
    )

def get_job_status(job_id: str) -> dict[str, object]:
    data = redis_client.get(f"job:{job_id}")
    if data:
        return from_json(data)
    return {"status": "not_found"}

def delete_job(job_id: str):
    redis_client.delete(f"job:{job_id}")


# DEDUPLICATION

def is_duplicate(key: str, ttl: int = 30) -> bool:
    result = redis_client.set(
        f"dedup:{key}",
        "1",
        nx=True,
        ex=ttl
    )
    return result is None

def clear_dedup(key: str):
    redis_client.delete(f"dedup:{key}")

# RATE LIMITING

def check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
    redis_key = f"rate:{key}"
    current   = redis_client.get(redis_key)

    if current is None:
        redis_client.setex(redis_key, window_seconds, 1)
        return True

    if int(current) < max_calls:
        redis_client.incr(redis_key)
        return True

    return False

def get_rate_limit_remaining(key: str, max_calls: int) -> int:
    current = redis_client.get(f"rate:{key}")
    if current is None:
        return max_calls
    return max(0, max_calls - int(current))

# CACHING

def cache_set(key: str, data: object, ttl: int = 300) -> None:
    redis_client.setex(
        f"cache:{key}",
        ttl,
        to_json(data)
    )

def cache_get(key: str) -> object:
    data = redis_client.get(f"cache:{key}")
    if data:
        return from_json(data)
    return None

def cache_delete(key: str):
    redis_client.delete(f"cache:{key}")



# HEALTH CHECK
 
def redis_health() -> bool:
    try:
        result = redis_client.ping()
        return bool(result)
    except Exception:
        return False