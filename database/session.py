"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

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


def _engine_pool_options() -> dict[str, Any]:
    """Choose a pool strategy compatible with the hosting event-loop lifecycle.

    Vercel may reuse a warm serverless process across different event loops.
    Async pooled connections must not be transferred between event loops, so
    Vercel uses NullPool. Each checked-out connection nevertheless remains
    open for its complete context-manager lifetime, preserving PostgreSQL
    session advisory locks used to serialize webhook updates.
    """
    if os.getenv("VERCEL") == "1":
        return {"poolclass": NullPool}

    return {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_recycle": 1800,
    }


DATABASE_URL = _get_database_url()

if DATABASE_URL.startswith("postgresql+psycopg://"):
    _connect_args: dict[str, Any] = {"connect_timeout": 5}
else:
    _connect_args = {"timeout": 5, "command_timeout": 30}

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args,
    future=True,
    **_engine_pool_options(),
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
