"""User repository."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import User, Role

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence operations for users."""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _with_rbac(self, statement):
        """Eagerly load roles and permissions for async-safe authorization."""
        return statement.options(
            selectinload(User.roles).selectinload(Role.permissions)
        )

    async def get_by_id(self, entity_id):
        """Get a user with roles and permissions loaded."""
        result = await self.session.execute(
            self._with_rbac(
                select(User).where(User.id == entity_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.telegram_user_id == telegram_user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            self._with_rbac(
                select(User).where(User.username == username)
            )
        )
        return result.scalar_one_or_none()
