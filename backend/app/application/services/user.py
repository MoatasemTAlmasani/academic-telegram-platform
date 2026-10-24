"""User application service."""

from __future__ import annotations

from uuid import UUID

from database.models.identity import User

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class UserService:
    """Application use cases related to users."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.uow.users.get_by_id(user_id)

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> User | None:
        return await self.uow.users.get_by_telegram_user_id(
            telegram_user_id
        )

    async def get_by_email(self, email: str) -> User | None:
        return await self.uow.users.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        return await self.uow.users.get_by_username(username)

    async def create(self, user: User) -> User:
        created = await self.uow.users.add(user)
        await self.uow.commit()
        return created
