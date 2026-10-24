"""Database session access."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from database.session import SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an application database session."""
    async with SessionLocal() as session:
        yield session
