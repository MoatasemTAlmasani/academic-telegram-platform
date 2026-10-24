"""Notification application service."""

from __future__ import annotations

from uuid import UUID

from database.models.notifications import Notification

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class NotificationService:
    """Application use cases for notifications."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        notification_id: UUID,
    ) -> Notification | None:
        return await self.uow.notifications.get_by_id(
            notification_id
        )

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[Notification]:
        return await self.uow.notifications.get_by_user_id(user_id)

    async def create(
        self,
        notification: Notification,
    ) -> Notification:
        created = await self.uow.notifications.add(notification)
        await self.uow.commit()
        return created
