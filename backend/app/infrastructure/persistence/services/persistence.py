"""Persistence service factory."""

from sqlalchemy.ext.asyncio import AsyncSession

from ..unit_of_work import UnitOfWork


def create_unit_of_work(session: AsyncSession) -> UnitOfWork:
    """Create a Unit of Work for the current request."""
    return UnitOfWork(session)
