from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import time

from app.db import engine
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    """
    Basic health check endpoint.
    Returns simple status for load balancer health checks.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/live")
def live():
    """
    Liveness probe - checks if the application is running.
    Used by Kubernetes to restart unhealthy containers.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
def ready():
    """
    Readiness probe - checks if the application is ready to serve traffic.
    Checks database connectivity and other dependencies.
    """
    checks = {}
    all_healthy = True
    
    # Database check
    try:
        start = time.time()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_latency = (time.time() - start) * 1000  # Convert to ms
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False
    
    # Cache check (placeholder - implement when Redis is configured)
    try:
        # TODO: Add actual Redis health check
        checks["cache"] = {
            "status": "healthy",
            "note": "Cache not configured, skipping check",
        }
    except Exception as e:
        checks["cache"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False
    
    # Task queue check (placeholder - implement when Celery is configured)
    try:
        # TODO: Add actual Celery health check
        checks["task_queue"] = {
            "status": "healthy",
            "note": "Task queue not configured, skipping check",
        }
    except Exception as e:
        checks["task_queue"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False
    
    status = "ready" if all_healthy else "not_ready"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


@router.get("/detailed")
def detailed():
    """
    Detailed health check with additional system information.
    Includes version, uptime, and resource usage hints.
    """
    # TODO: Add actual system metrics collection
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",  # TODO: Get from version file
        "environment": "development",  # TODO: Get from environment
        "checks": {
            "database": "ok",
            "cache": "not_configured",
            "task_queue": "not_configured",
        },
        "metrics": {
            # TODO: Add actual metrics from metrics_service
            "api_requests_total": 0,
            "active_users": 0,
        },
    }


@router.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format for scraping.
    """
    # TODO: Return actual Prometheus metrics when prometheus-client is configured
    # from prometheus_client import generate_latest
    # return Response(generate_latest(), media_type="text/plain")
    
    # Return in-memory metrics for now
    return metrics_service.get_metrics()



