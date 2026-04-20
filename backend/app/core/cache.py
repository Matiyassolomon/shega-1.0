"""
Redis caching layer for improved performance and scalability.
"""

import os
import json
import pickle
from typing import Any, Optional, Union
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Try to import redis, fallback to in-memory if not available
try:
    import redis
    from redis.exceptions import RedisError, ConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed, using in-memory cache fallback")

class CacheConfig:
    """Cache configuration with Redis support."""
    
    def __init__(self):
        self.enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.default_ttl = int(os.getenv("REDIS_DEFAULT_TTL", "3600"))  # 1 hour
        self.connection_timeout = int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5"))
        
    def is_configured(self) -> bool:
        """Check if Redis is properly configured."""
        return self.enabled and REDIS_AVAILABLE

# Global configuration
cache_config = CacheConfig()

class CacheManager:
    """Universal cache manager supporting Redis and in-memory fallback."""
    
    def __init__(self):
        self._redis_client = None
        self._memory_cache = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Redis client or fallback to memory."""
        if cache_config.is_configured():
            try:
                self._redis_client = redis.Redis(
                    host=cache_config.host,
                    port=cache_config.port,
                    db=cache_config.db,
                    password=cache_config.password,
                    socket_timeout=cache_config.connection_timeout,
                    socket_connect_timeout=cache_config.connection_timeout,
                    decode_responses=True,
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        else:
            logger.info("Using in-memory cache")
    
    def _get_key(self, key: str, prefix: str = "music_platform") -> str:
        """Generate namespaced cache key."""
        return f"{prefix}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self._redis_client:
                full_key = self._get_key(key)
                value = self._redis_client.get(full_key)
                if value:
                    return json.loads(value)
                return default
            else:
                # In-memory cache
                return self._memory_cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or cache_config.default_ttl
            
            if self._redis_client:
                full_key = self._get_key(key)
                serialized = json.dumps(value, default=str)
                self._redis_client.setex(full_key, ttl, serialized)
                return True
            else:
                # In-memory cache (no TTL support)
                self._memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self._redis_client:
                full_key = self._get_key(key)
                self._redis_client.delete(full_key)
                return True
            else:
                self._memory_cache.pop(key, None)
                return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self, pattern: str = "*") -> bool:
        """Clear cache by pattern."""
        try:
            if self._redis_client:
                full_pattern = self._get_key(pattern)
                keys = self._redis_client.keys(full_pattern)
                if keys:
                    self._redis_client.delete(*keys)
                return True
            else:
                self._memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self._redis_client:
                full_key = self._get_key(key)
                return self._redis_client.exists(full_key) > 0
            else:
                return key in self._memory_cache
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def get_or_set(self, key: str, factory: callable, ttl: Optional[int] = None) -> Any:
        """Get from cache or compute and store if not exists."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def health_check(self) -> dict:
        """Check cache health status."""
        try:
            if self._redis_client:
                self._redis_client.ping()
                info = self._redis_client.info()
                return {
                    "status": "healthy",
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                }
            else:
                return {
                    "status": "healthy",
                    "type": "memory",
                    "keys_count": len(self._memory_cache),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

# Global cache instance
cache = CacheManager()

# Decorator for function result caching
def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Compute and store
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, stored result")
            return result
        return wrapper
    return decorator

# Specific cache helpers for common operations
class MusicPlatformCache:
    """Specialized cache operations for music platform."""
    
    @staticmethod
    def cache_recommendations(user_id: str, recommendations: Any, ttl: int = 1800):
        """Cache user recommendations for 30 minutes."""
        key = f"recommendations:{user_id}"
        cache.set(key, recommendations, ttl)
    
    @staticmethod
    def get_recommendations(user_id: str) -> Optional[Any]:
        """Get cached recommendations."""
        key = f"recommendations:{user_id}"
        return cache.get(key)
    
    @staticmethod
    def cache_marketplace_items(items: Any, ttl: int = 600):
        """Cache marketplace items for 10 minutes."""
        cache.set("marketplace:items", items, ttl)
    
    @staticmethod
    def get_marketplace_items() -> Optional[Any]:
        """Get cached marketplace items."""
        return cache.get("marketplace:items")
    
    @staticmethod
    def cache_payment_status(payment_id: str, status: Any, ttl: int = 300):
        """Cache payment status for 5 minutes."""
        key = f"payment:status:{payment_id}"
        cache.set(key, status, ttl)
    
    @staticmethod
    def get_payment_status(payment_id: str) -> Optional[Any]:
        """Get cached payment status."""
        key = f"payment:status:{payment_id}"
        return cache.get(key)
    
    @staticmethod
    def invalidate_user_cache(user_id: str):
        """Invalidate all cache for a specific user."""
        patterns = [
            f"recommendations:{user_id}",
            f"user:{user_id}:*",
        ]
        for pattern in patterns:
            cache.clear(pattern)
    
    @staticmethod
    def clear_all_cache():
        """Clear all application cache."""
        cache.clear("music_platform:*")

# Export cache utilities
__all__ = [
    "cache",
    "CacheManager",
    "MusicPlatformCache",
    "cached",
    "cache_config",
]
