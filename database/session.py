
"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import get_settings
from database.url import normalize_async_database_url


def _get_database_url() -> str:
    """Return the configured database URL or fail with a clear message."""
    database_url = get_settings().database_url

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set database_url in the environment before using the database."
        )

    return normalize_async_database_url(database_url)


DATABASE_URL = _get_database_url()

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_timeout=10,
    pool_recycle=1800,
    connect_args=(
        {"connect_timeout": 5}
        if DATABASE_URL.startswith("postgresql+psycopg://")
        else {"timeout": 5, "command_timeout": 30}
    ),
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for application use."""
    async with SessionLocal() as session:
        yield session