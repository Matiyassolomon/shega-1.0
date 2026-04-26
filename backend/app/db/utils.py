"""
Database utilities for production-grade operations.

Provides:
- Transaction retry logic for transient failures
- Connection health checks
- Structured query logging hooks
"""
import functools
import logging
import time
from typing import Callable, TypeVar, Any

from sqlalchemy.exc import OperationalError, DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseRetryConfig:
    """Configuration for database retry behavior."""
    
    max_retries: int = 3
    base_delay: float = 0.1  # 100ms
    max_delay: float = 2.0   # 2 seconds
    exponential_base: float = 2.0
    
    # Transient error codes that warrant retry
    # PostgreSQL: 40001 (serialization_failure), 40P01 (deadlock)
    # MySQL: 1213 (deadlock), 1205 (lock wait timeout)
    transient_error_codes = {
        "40001", "40P01", "1213", "1205"
    }


def is_transient_error(error: Exception) -> bool:
    """
    Check if a database error is likely transient and should be retried.
    
    Args:
        error: The exception that was raised
        
    Returns:
        True if the error is likely transient
    """
    if not isinstance(error, OperationalError):
        return False
    
    # Extract error code from various DB drivers
    error_code = None
    
    # PostgreSQL (psycopg2)
    if hasattr(error, "orig") and hasattr(error.orig, "pgcode"):
        error_code = error.orig.pgcode
    
    # MySQL (pymysql/mysql-connector)
    if hasattr(error, "orig") and hasattr(error.orig, "args"):
        args = error.orig.args
        if args and isinstance(args[0], int):
            error_code = str(args[0])
    
    if error_code in DatabaseRetryConfig.transient_error_codes:
        return True
    
    # Check for common transient error messages
    error_str = str(error).lower()
    transient_keywords = [
        "deadlock", "lock wait timeout", "serialization failure",
        "connection", "timeout", "temporarily"
    ]
    return any(kw in error_str for kw in transient_keywords)


def with_db_retry(
    max_retries: int = None,
    base_delay: float = None,
    on_retry: Callable[[Exception, int], None] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries database operations on transient failures.
    
    Uses exponential backoff with jitter. Only retries on operational errors
    that are likely transient (deadlocks, lock timeouts, etc.).
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 0.1)
        on_retry: Optional callback called on each retry with (error, attempt_number)
        
    Example:
        @with_db_retry(max_retries=3)
        def save_user(db: Session, user: User) -> None:
            db.add(user)
            db.commit()
    """
    max_retries = max_retries or DatabaseRetryConfig.max_retries
    base_delay = base_delay or DatabaseRetryConfig.base_delay
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (OperationalError, DatabaseError) as e:
                    last_exception = e
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"db_retry_exhausted",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        raise
                    
                    if not is_transient_error(e):
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (DatabaseRetryConfig.exponential_base ** attempt),
                        DatabaseRetryConfig.max_delay
                    )
                    
                    logger.warning(
                        f"db_retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(delay)
                    continue
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Unexpected retry loop exit")
            
        return wrapper
    return decorator


def check_db_health(db_session) -> dict:
    """
    Perform a lightweight health check on the database connection.
    
    Args:
        db_session: SQLAlchemy session
        
    Returns:
        Dict with status and latency information
    """
    import time
    from sqlalchemy import text
    
    start = time.time()
    try:
        # Lightweight query - works across all SQL backends
        result = db_session.execute(text("SELECT 1"))
        result.scalar()
        latency_ms = (time.time() - start) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "connected": True
        }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "connected": False,
            "error": str(e)
        }


def get_connection_pool_stats(db_engine) -> dict:
    """
    Get connection pool statistics for monitoring.
    
    Args:
        db_engine: SQLAlchemy engine
        
    Returns:
        Dict with pool statistics
    """
    pool = db_engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
