"""Telegram application service."""

from __future__ import annotations

from database.models.telegram import TelegramDestination

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class TelegramService:
    """Application use cases for Telegram destinations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_chat_id(
        self,
        chat_id: int,
    ) -> TelegramDestination | None:
        return await self.uow.telegram_destinations.get_by_chat_id(
            chat_id
        )

    async def create(
        self,
        destination: TelegramDestination,
    ) -> TelegramDestination:
        created = await self.uow.telegram_destinations.add(destination)
        await self.uow.commit()
        return created
