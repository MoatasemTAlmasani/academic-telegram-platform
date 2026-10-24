"""Quote repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.quotes import Quote

from .base import BaseRepository


class QuoteRepository(BaseRepository[Quote]):
    """Persistence operations for quotes."""

    model = Quote

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_request_id(
        self,
        request_id: UUID,
    ) -> list[Quote]:
        result = await self.session.execute(
            select(Quote).where(
                Quote.request_id == request_id
            )
        )
        return list(result.scalars().all())
