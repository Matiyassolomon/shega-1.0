 """
Payment domain main module.

This module initializes the payment domain with all its components
and provides the main FastAPI application for the payment service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import get_settings
from apps.payments.api.routers import router as payment_router
from apps.payments.config import get_payment_config, initialize_payment_providers
from apps.payments.services.payment_service import PaymentService
from apps.payments.services.webhook_service import WebhookService
from shared.db import get_db, create_tables
from shared.logging import configure_logging, get_logger
from shared.middleware import create_middleware_stack

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Payment application starting up")
    
    # Initialize database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Initialize payment providers
    try:
        providers = initialize_payment_providers()
        logger.info(f"Initialized {len(providers)} payment providers: {list(providers.keys())}")
        
        # Store providers in app state for dependency injection
        app.state.payment_providers = providers
        app.state.payment_config = get_payment_config()
        
    except Exception as e:
        logger.error(f"Failed to initialize payment providers: {e}")
        raise
    
    logger.info("Payment application startup complete")
    yield
    logger.info("Payment application shutting down")


# Create FastAPI application
app = FastAPI(
    title="Payment Service",
    description="Reusable payment processing service for Ethiopian and international payments",
    version="1.0.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.redoc_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

# Add middleware stack
create_middleware_stack(app, include_rate_limiting=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "X-Admin-Key", 
        "X-Request-ID",
        "X-Idempotency-Key",
        "X-Signature",
        "X-Webhook-Signature",
    ],
)

# Include payment router
app.include_router(payment_router)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "payment"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check with provider validation."""
    try:
        # Check database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        # Check payment providers
        payment_config = app.state.payment_config
        validation_results = payment_config.validate_provider_configs()
        
        failed_providers = [
            provider for provider, is_valid in validation_results.items() 
            if not is_valid
        ]
        
        if failed_providers:
            return {
                "status": "degraded",
                "service": "payment",
                "database": "healthy",
                "providers": validation_results,
                "failed_providers": failed_providers
            }
        
        return {
            "status": "ready",
            "service": "payment",
            "database": "healthy",
            "providers": validation_results,
            "available_providers": payment_config.get_available_providers()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "payment",
                "error": str(e)
            }
        )


@app.get("/health/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive", "service": "payment"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Payment Service",
        "version": "1.0.0",
        "description": "Reusable payment processing service",
        "docs_url": "/docs" if settings.docs_enabled else None,
        "health_check": "/health",
        "providers": app.state.payment_config.get_available_providers(),
        "environment": settings.app_env,
    }


# Provider information endpoint
@app.get("/providers")
async def list_providers():
    """List available payment providers."""
    payment_config = app.state.payment_config
    
    providers_info = {}
    for provider_name in payment_config.get_available_providers():
        config = payment_config.get_provider_config(provider_name)
        providers_info[provider_name] = {
            "name": provider_name,
            "configured": True,
            "test_mode": config.get("test_mode", True),
            "supported_currencies": ["ETB"],  # Would be dynamic from provider
        }
    
    return {
        "providers": providers_info,
        "total_count": len(providers_info)
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Value error handler."""
    logger.warning(
        "Value error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_request",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(KeyError)
async def key_error_handler(request, exc):
    """Key error handler."""
    logger.warning(
        "Key error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "missing_field",
            "message": f"Required field is missing: {str(exc)}",
            "request_id": getattr(request.state, "request_id", None),
        }
    )


# Dependency injection functions
def get_payment_service(db=Depends(get_db)) -> PaymentService:
    """Get payment service with providers."""
    service = PaymentService(db)
    
    # Register all available providers
    for provider_name, provider in app.state.payment_providers.items():
        service.register_provider(provider)
    
    return service


def get_webhook_service(db=Depends(get_db)) -> WebhookService:
    """Get webhook service with providers."""
    service = WebhookService(db)
    
    # Register all available providers
    for provider_name, provider in app.state.payment_providers.items():
        service.register_provider(provider)
    
    return service


# Override the dependency functions in the routers
import apps.payments.api.routers as payment_routers

payment_routers.get_payment_service = get_payment_service
payment_routers.get_webhook_service = get_webhook_service


# Development utilities
if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "apps.payments.main:app",
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflicts
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


# Export main components
__all__ = [
    "app",
    "get_payment_service",
    "get_webhook_service",
]
