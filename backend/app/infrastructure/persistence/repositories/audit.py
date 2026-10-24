"""Audit log repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.audit import AuditLog

from .base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Persistence operations for audit events."""

    model = AuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_actor_id(
        self,
        actor_id: UUID,
    ) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).where(
                AuditLog.actor_id == actor_id
            )
        )
        return list(result.scalars().all())
