from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine
from app.core.redis import redis_client
from app.core.security.middleware import SecurityMiddleware
from app.core.rate_limiter import rate_limiter
from app.api.routers import auth, users, playback, wallet, payments, webhooks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Shega API...")
    await redis_client.connect()
    logger.info("✅ Redis connected")
    
    async with engine.connect() as conn:
        await conn.execute("SELECT 1")
    logger.info("✅ Database connected")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await engine.dispose()
    await redis_client.close()

app = FastAPI(
    title="Shega Music Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DOCS_ENABLED else None,
)

# Middleware (order matters)
app.add_middleware(SecurityMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Health endpoints
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/readiness")
async def readiness():
    checks = {
        "database": False,
        "redis": False,
    }
    
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        await redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        return {"status": "not_ready", "checks": checks}

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(playback.router, prefix="/api/v1/playback", tags=["playback"])
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["wallet"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])