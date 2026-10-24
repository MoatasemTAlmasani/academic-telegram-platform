"""Quote application service."""

from __future__ import annotations

from uuid import UUID

from database.models.quotes import Quote

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class QuoteService:
    """Application use cases for service quotations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(self, quote_id: UUID) -> Quote | None:
        return await self.uow.quotes.get_by_id(quote_id)

    async def get_by_request_id(
        self,
        request_id: UUID,
    ) -> list[Quote]:
        return await self.uow.quotes.get_by_request_id(request_id)

    async def create(self, quote: Quote) -> Quote:
        created = await self.uow.quotes.add(quote)
        await self.uow.commit()
        return created
