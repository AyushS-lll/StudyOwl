"""
Database initialization and session management.

Async SQLAlchemy engine and session factory for PostgreSQL.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from config import settings

# Base class for all models
Base = declarative_base()

# Async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    future=True,
)

# Async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables and set up connection pool."""
    # Import models here to ensure they're registered with Base
    from models import Student, Session, Attempt  # noqa: F401

    async with engine.begin() as conn:
        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)

        # Idempotent in-place migrations for existing deployments where
        # create_all only adds new tables, not new columns on existing ones.
        if conn.dialect.name == "postgresql":
            await conn.execute(text(
                "ALTER TABLE sessions "
                "ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ "
                "NOT NULL DEFAULT NOW()"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_sessions_last_activity_at "
                "ON sessions (last_activity_at)"
            ))


async def get_db() -> AsyncSession:
    """Dependency: yields an async DB session for each request."""
    async with SessionLocal() as session:
        yield session


async def close_db() -> None:
    """Close the database engine."""
    await engine.dispose()
