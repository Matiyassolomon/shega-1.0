from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routers import (
    admin_holidays_router,
    audio_analysis_router,
    calendar_router,
    core_router,
    marketplace_router,
    payments_router,
)
from app.api.v1 import api_router as api_v1_router
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.core.logging import configure_logging, get_logger
from app.core.settings import get_settings
from app.core.middleware import RequestIDMiddleware, TimingMiddleware, SecurityHeadersMiddleware, get_request_id
from app.db import Base, SessionLocal, engine
from app.db.utils import check_db_health, get_connection_pool_stats
from app.middleware import (
    CacheMiddleware,
    MaxRequestSizeMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
)
from app.services import crud

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


def _validate_startup_schema() -> None:
    """Validate required tables exist. Warns about mismatches but never alters schema at runtime."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        "users", "subscriptions", "playback_events", "sessions",
        "library_songs", "stream_sessions", "song_purchases", "song_marketplace"
    }
    missing = required_tables - existing_tables
    if missing:
        logger.warning(
            "startup_schema_missing_tables",
            missing_tables=sorted(missing),
            message="Run migrations to create missing tables"
        )
    else:
        logger.info("startup_schema_validated", tables_count=len(existing_tables))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("application_startup")
    # Create tables for local/dev only; production should use migrations
    if settings.is_sqlite or settings.app_env == "development":
        Base.metadata.create_all(bind=engine)
    _validate_startup_schema()
    db = SessionLocal()
    try:
        crud.ensure_seed_data(db)
    finally:
        db.close()
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.redoc_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

# Add middleware in correct order
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key", "X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    MaxRequestSizeMiddleware, max_body_size=settings.max_upload_size_bytes
)
app.add_middleware(
    RateLimitMiddleware, 
    requests_per_minute=getattr(settings, 'rate_limit_per_minute', 60)
)
app.add_middleware(CacheMiddleware, cache_ttl=300)
app.add_middleware(RequestContextMiddleware)

if settings.https_redirect:
    app.add_middleware(HTTPSRedirectMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        request_id=getattr(request.state, "request_id", None),
        path=request.url.path
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        request_id=getattr(request.state, "request_id", None),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.get("/")
def root():
    return {
        "message": "Music Platform Backend Running",
        "environment": settings.app_env,
        "version": settings.app_version,
    }


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}


@app.get("/health/live")
def liveness():
    """
    Kubernetes liveness probe.
    Returns 200 if the process is alive and can accept requests.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe.
    Returns 200 only when all dependencies are healthy (database, cache).
    """
    # Check database health
    db_health = check_db_health(db)
    
    if not db_health.get("connected"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": db_health,
                "request_id": get_request_id()
            }
        )
    
    # Check cache health
    from app.core.cache import cache
    cache_health = cache.health_check()
    
    return {
        "status": "ready",
        "database": db_health,
        "cache": cache_health,
        "pool": get_connection_pool_stats(engine),
        "request_id": get_request_id(),
        "timestamp": datetime.utcnow().isoformat()
    }


app.include_router(core_router)
app.include_router(marketplace_router)
app.include_router(payments_router)
app.include_router(calendar_router)
app.include_router(api_v1_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_holidays_router)
app.include_router(audio_analysis_router)

# Add observability middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)

# Add security headers middleware
from app.core.middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
