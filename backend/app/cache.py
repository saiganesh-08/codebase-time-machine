import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_client = redis.from_url(REDIS_URL, decode_responses=True)

DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour


def get_json(key: str):
    raw = _client.get(key)
    return json.loads(raw) if raw else None


def set_json(key: str, value, ttl: int = DEFAULT_TTL_SECONDS):
    _client.set(key, json.dumps(value), ex=ttl)


def invalidate(prefix: str):
    for key in _client.scan_iter(f"{prefix}*"):
        _client.delete(key)
