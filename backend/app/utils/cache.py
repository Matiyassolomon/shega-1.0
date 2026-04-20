from collections.abc import Callable
import json
from time import time
from typing import Generic, TypeVar

from app.core.settings import get_settings

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Small in-memory helper for inexpensive process-local caching."""

    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        value = self._store.get(key)
        if value is None:
            return None
        expires_at, payload = value
        if expires_at < time():
            self._store.pop(key, None)
            return None
        return payload

    def set(self, key: str, value: T) -> None:
        self._store[key] = (time() + self.ttl_seconds, value)

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value)
        return value


class CacheClient:
    """Uses Redis when configured, otherwise falls back to process-local TTL caching."""

    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self.memory_cache: TTLCache[object] = TTLCache(ttl_seconds)
        self.redis_client = self._build_redis_client()

    def _build_redis_client(self):
        settings = get_settings()
        if not settings.redis_url:
            return None
        try:
            import redis

            return redis.Redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            return None

    def get(self, key: str):
        if self.redis_client is not None:
            try:
                cached = self.redis_client.get(key)
                if cached is not None:
                    return json.loads(cached)
            except Exception:
                pass
        return self.memory_cache.get(key)

    def set(self, key: str, value):
        if self.redis_client is not None:
            try:
                self.redis_client.setex(key, self.ttl_seconds, json.dumps(value, default=str))
                return
            except Exception:
                pass
        self.memory_cache.set(key, value)
