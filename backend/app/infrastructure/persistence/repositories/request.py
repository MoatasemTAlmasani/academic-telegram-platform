"""Service request repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.requests import ServiceRequest

from .base import BaseRepository


class ServiceRequestRepository(BaseRepository[ServiceRequest]):
    """Persistence operations for service requests."""

    model = ServiceRequest

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_customer_id(
        self,
        customer_id: UUID,
    ) -> list[ServiceRequest]:
        result = await self.session.execute(
            select(ServiceRequest).where(
                ServiceRequest.customer_id == customer_id
            )
        )
        return list(result.scalars().all())

    async def get_by_service_id(
        self,
        service_id: UUID,
    ) -> list[ServiceRequest]:
        result = await self.session.execute(
            select(ServiceRequest).where(
                ServiceRequest.service_id == service_id
            )
        )
        return list(result.scalars().all())
