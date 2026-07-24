"""Optional Redis cache. SQL remains authoritative and Redis failures are non-fatal."""
import json
import os

def _client():
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True, socket_connect_timeout=0.5)
    except Exception:
        return None

def get_json(key: str):
    try:
        client = _client(); value = client.get(key) if client else None
        return json.loads(value) if value else None
    except Exception:
        return None

def set_json(key: str, value, ttl: int = 900):
    try:
        client = _client()
        if client: client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass

def delete(key: str):
    try:
        client = _client()
        if client: client.delete(key)
    except Exception:
        pass
