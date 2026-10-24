"""Telegram persistence repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.telegram import TelegramDestination

from .base import BaseRepository


class TelegramDestinationRepository(
    BaseRepository[TelegramDestination]
):
    """Persistence operations for Telegram destinations."""

    model = TelegramDestination

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_chat_id(
        self,
        chat_id: int,
    ) -> TelegramDestination | None:
        result = await self.session.execute(
            select(TelegramDestination).where(
                TelegramDestination.chat_id == chat_id
            )
        )
        return result.scalar_one_or_none()
