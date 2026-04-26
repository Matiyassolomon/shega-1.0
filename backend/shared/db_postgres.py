# shared/db.py - PostgreSQL with connection pooling
import os
from contextlib import contextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool, NullPool

# Base class for all models
Base = declarative_base()

# Connection pool configuration
POOL_SIZE = int(os.getenv(\"DB_POOL_SIZE\", \"10\"))
MAX_OVERFLOW = int(os.getenv(\"DB_MAX_OVERFLOW\", \"20\"))
POOL_TIMEOUT = int(os.getenv(\"DB_POOL_TIMEOUT\", \"30\"))
POOL_RECYCLE = int(os.getenv(\"DB_POOL_RECYCLE\", \"3600\"))  # 1 hour


def get_database_url() -> str:
    \"\"\"
    Get database URL from environment.
    Supports both sync (psycopg2) and async (asyncpg) URLs.
    \"\"\"
    db_url = os.getenv(\n        \"DATABASE_URL\",
        \"postgresql://postgres:postgres@localhost:5432/shega_payments\"
    )
    return db_url


def get_async_database_url() -> str:
    \"\"\"
    Convert sync URL to async URL.
    postgresql:// -> postgresql+asyncpg://
    \"\"\"
    url = get_database_url()
    if url.startswith(\"postgresql://\"):
        return url.replace(\"postgresql://\", \"postgresql+asyncpg://\", 1)
    return url


# Sync Engine with connection pooling
def get_sync_engine() -> Engine:
    \"\"\"
    Create synchronous database engine with connection pooling.
    Use for background tasks and non-async operations.
    \"\"\"
    db_url = get_database_url()
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before use
        echo=os.getenv(\"SQL_DEBUG\", \"false\").lower() == \"true\"
    )
    
    # Add event listeners for connection monitoring
    @event.listens_for(engine, \"connect\")
    def on_connect(dbapi_conn, connection_record):
        pass  # Could log connection establishment
    
    @event.listens_for(engine, \"checkout\")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        pass  # Could log connection checkout
    
    return engine


# Async Engine with connection pooling
def get_async_engine():
    \"\"\"
    Create asynchronous database engine with connection pooling.
    Use for FastAPI endpoints and async operations.
    \"\"\"
    db_url = get_async_database_url()
    
    return create_async_engine(
        db_url,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,
        echo=os.getenv(\"SQL_DEBUG\", \"false\").lower() == \"true\"
    )


# Sync Session Factory
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_sync_engine()
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


# Context manager for sync sessions
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    \"\"\"
    Context manager for synchronous database sessions.
    
    Usage:
        with get_db_session() as db:
            payment = db.query(Payment).first()
    \"\"\"
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Async dependency for FastAPI
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    \"\"\"
    FastAPI dependency for async database sessions.
    
    Usage:
        @router.get(\"/payments\")
        async def list_payments(db: AsyncSession = Depends(get_async_db)):
            pass
    \"\"\"
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Legacy support for existing code
SessionLocal = SyncSessionLocal


def init_db():
    \"\"\"
    Initialize database tables.
    Called on application startup.
    \"\"\"
    engine = get_sync_engine()
    Base.metadata.create_all(bind=engine)
