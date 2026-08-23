import redis.asyncio as redis
from typing import Optional, Any
import pickle
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self):
        if self._connected:
            return
        
        async with self._lock:
            if self._connected:
                return
            
            try:
                self.client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=False,
                    max_connections=50,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                )
                await self.client.ping()
                self._connected = True
                logger.info("✅ Redis connected")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                raise

    async def close(self):
        if self.client and self._connected:
            await self.client.close()
            self._connected = False
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        if not self._connected:
            return None
        try:
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        if not self._connected:
            return
        try:
            await self.client.setex(key, ttl, pickle.dumps(value))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        if self._connected:
            await self.client.delete(key)

    async def delete_pattern(self, pattern: str):
        if not self._connected:
            return
        try:
            cursor = 0
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=1000)
                if keys:
                    await self.client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Redis delete_pattern error: {e}")

    async def incr(self, key: str, amount: int = 1) -> int:
        if not self._connected:
            return 0
        return await self.client.incrby(key, amount)

    async def exists(self, key: str) -> bool:
        if not self._connected:
            return False
        return await self.client.exists(key) > 0

    async def expire(self, key: str, ttl: int):
        if self._connected:
            await self.client.expire(key, ttl)

    async def ttl(self, key: str) -> int:
        if not self._connected:
            return -1
        return await self.client.ttl(key)

    async def ping(self) -> bool:
        if not self._connected:
            return False
        try:
            return await self.client.ping()
        except:
            return False

redis_client = RedisClient()