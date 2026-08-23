from fastapi import Request, HTTPException
from typing import Optional
import time
from app.core.redis import redis_client
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.limits = {
            "auth_login": (5, 300),      # 5 attempts per 5 minutes
            "auth_register": (3, 3600),  # 3 per hour
            "auth_otp": (3, 600),        # 3 per 10 minutes
            "api_read": (1000, 60),      # 1000 per minute
            "api_write": (100, 60),      # 100 per minute
            "payment": (20, 60),         # 20 per minute
            "wallet": (50, 60),          # 50 per minute
        }

    async def check_rate_limit(
        self,
        request: Request,
        limit_type: str,
        user_id: Optional[str] = None
    ) -> bool:
        if limit_type not in self.limits:
            return True

        max_requests, period = self.limits[limit_type]
        
        # Determine key
        client_ip = request.client.host if request.client else "unknown"
        if user_id:
            rate_key = f"rate:{limit_type}:user:{user_id}"
        else:
            rate_key = f"rate:{limit_type}:ip:{client_ip}"
        
        current = await redis_client.incr(rate_key)
        if current == 1:
            await redis_client.expire(rate_key, period)
        
        if current > max_requests:
            ttl = await redis_client.ttl(rate_key)
            logger.warning(f"Rate limit exceeded: {limit_type} [{user_id or client_ip}]")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds."
            )
        
        return True

rate_limiter = RateLimiter()