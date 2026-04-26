"""
Production middleware for observability and request handling.

Provides:
- Request ID generation and propagation
- Structured request/response logging
- Request timing metrics
"""
import time
import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class RequestContext:
    """Thread-local request context for accessing request ID in any code path."""
    _request_id: Optional[str] = None
    
    @classmethod
    def set_request_id(cls, request_id: str):
        cls._request_id = request_id
    
    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return cls._request_id
    
    @classmethod
    def clear(cls):
        cls._request_id = None


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates and attaches a unique request ID to each request.
    
    The request ID is:
    - Generated if not provided in X-Request-ID header
    - Added to response headers as X-Request-ID
    - Stored in RequestContext for access throughout the request lifecycle
    - Included in all log entries via the request_id field
    
    This enables distributed tracing and request correlation across logs.
    """
    
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())[:16]  # Short but unique enough
        
        # Store in context for access in route handlers
        RequestContext.set_request_id(request_id)
        
        # Add to request state for dependency injection
        request.state.request_id = request_id
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers[self.header_name] = request_id
            
            # Log structured request info
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": self._get_client_ip(request),
                }
            )
            
            return response
            
        except Exception as e:
            # Log exception with request context
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": self._get_client_ip(request),
                    "error_type": type(e).__name__,
                }
            )
            raise
            
        finally:
            # Always clean up context
            RequestContext.clear()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        # Check X-Forwarded-For header first (common for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds timing information to response headers.
    
    Adds X-Response-Time header with duration in milliseconds.
    This helps clients monitor API latency.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return RequestContext.get_request_id()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff (prevents MIME sniffing)
    - X-Frame-Options: DENY (prevents clickjacking)
    - X-XSS-Protection: 1; mode=block (legacy XSS protection)
    - Strict-Transport-Security: max-age=31536000 (forces HTTPS)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: Restricts resource loading
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Legacy XSS protection (belt and suspenders)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS for 1 year (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Restrict resource loading (CSP)
        # Allow only self for scripts/styles, images from anywhere
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "media-src 'self' https:; "
            "connect-src 'self' https:;"
        )
        
        return response
