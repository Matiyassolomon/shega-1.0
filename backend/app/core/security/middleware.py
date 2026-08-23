from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import re
import hashlib
import time
import logging
from datetime import datetime
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    SQL_INJECTION_PATTERNS = [
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"('|\")?(OR|AND).*=.*('|\")",
    ]
    
    XSS_PATTERNS = [
        r"<script.*?>.*?</script.*?>",
        r"javascript:",
        r"onerror=",
        r"onload=",
    ]

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Validate request
        try:
            await self._validate_request(request)
        except Exception as e:
            logger.warning(f"Request validation failed: {e}")
            return Response("Invalid request", status_code=400)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

    async def _validate_request(self, request: Request):
        # Check query parameters
        for key, value in request.query_params.items():
            self._check_for_malicious_patterns(str(value))
        
        # Check body if JSON
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.json()
                await self._check_json_body(body)
            except:
                pass

    def _check_for_malicious_patterns(self, text: str):
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("SQL injection pattern detected")
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("XSS pattern detected")

    async def _check_json_body(self, body: dict):
        if isinstance(body, dict):
            for key, value in body.items():
                self._check_for_malicious_patterns(str(key))
                if isinstance(value, str):
                    self._check_for_malicious_patterns(value)
                elif isinstance(value, dict):
                    await self._check_json_body(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            self._check_for_malicious_patterns(item)
                        elif isinstance(item, dict):
                            await self._check_json_body(item)