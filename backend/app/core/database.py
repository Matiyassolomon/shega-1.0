"""
Database configuration with PostgreSQL support and connection pooling.
"""

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Database configuration
class DatabaseConfig:
    """Database configuration with support for SQLite (dev) and PostgreSQL (prod)."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./music_platform.db")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
        self.echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return "postgresql" in self.database_url.lower()
    
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return "sqlite" in self.database_url.lower()
    
    def get_async_url(self) -> str:
        """Get async database URL for PostgreSQL."""
        if self.is_postgres():
            # Convert postgres:// to postgresql+asyncpg://
            url = self.database_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return self.database_url

# Global configuration instance
db_config = DatabaseConfig()

# Create engine with appropriate configuration
def create_database_engine() -> Engine:
    """Create SQLAlchemy engine with connection pooling."""
    
    if db_config.is_sqlite():
        # SQLite configuration
        engine = create_engine(
            db_config.database_url,
            echo=db_config.echo,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL configuration with connection pooling
        engine = create_engine(
            db_config.database_url,
            echo=db_config.echo,
            poolclass=QueuePool,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            pool_timeout=db_config.pool_timeout,
            pool_recycle=db_config.pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
        )
    
    # Add event listeners for connection monitoring
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, connection_record):
        logger.debug("Database connection established")
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.debug("Database connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_conn, connection_record):
        logger.debug("Database connection returned to pool")
    
    return engine

# Create async engine for PostgreSQL
def create_async_engine_instance():
    """Create async SQLAlchemy engine for PostgreSQL."""
    if not db_config.is_postgres():
        return None
    
    async_url = db_config.get_async_url()
    
    return create_async_engine(
        async_url,
        echo=db_config.echo,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_timeout=db_config.pool_timeout,
        pool_recycle=db_config.pool_recycle,
        pool_pre_ping=True,
    )

# Create session factory
def create_session_factory(engine: Engine):
    """Create session factory with session management."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

# Create scoped session for thread safety
def create_scoped_session(session_factory):
    """Create thread-safe scoped session."""
    return scoped_session(session_factory)

# Context manager for database sessions
@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup."""
    from app.db import SessionLocal
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

# Async session context manager (for PostgreSQL)
async def get_async_session() -> AsyncSession:
    """Get async database session for PostgreSQL."""
    if not db_config.is_postgres():
        raise RuntimeError("Async sessions only available with PostgreSQL")
    
    async_engine = create_async_engine_instance()
    if not async_engine:
        raise RuntimeError("Failed to create async engine")
    
    async_session = sessionmaker(
        async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()

# Database migration utilities
def check_database_health(engine: Engine) -> dict:
    """Check database health and connection status."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {
                "status": "healthy",
                "database_type": "postgresql" if db_config.is_postgres() else "sqlite",
                "pool_size": db_config.pool_size,
                "connection_successful": True
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection_successful": False
        }

def get_database_stats(engine: Engine) -> dict:
    """Get database connection pool statistics."""
    if not db_config.is_postgres():
        return {"database_type": "sqlite", "pool_stats": "not_available"}
    
    pool = engine.pool
    return {
        "database_type": "postgresql",
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
