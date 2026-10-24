"""Notification repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.notifications import Notification

from .base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Persistence operations for notifications."""

    model = Notification

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification).where(
                Notification.user_id == user_id
            )
        )
        return list(result.scalars().all())
