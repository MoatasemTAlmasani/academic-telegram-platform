"""Service request application service."""

from __future__ import annotations

from uuid import UUID

from database.models.requests import ServiceRequest

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class ServiceRequestService:
    """Application use cases for customer service requests."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        request_id: UUID,
    ) -> ServiceRequest | None:
        return await self.uow.requests.get_by_id(request_id)

    async def get_by_customer_id(
        self,
        customer_id: UUID,
    ) -> list[ServiceRequest]:
        return await self.uow.requests.get_by_customer_id(
            customer_id
        )

    async def get_by_service_id(
        self,
        service_id: UUID,
    ) -> list[ServiceRequest]:
        return await self.uow.requests.get_by_service_id(
            service_id
        )

    async def create(
        self,
        request: ServiceRequest,
    ) -> ServiceRequest:
        created = await self.uow.requests.add(request)
        await self.uow.commit()
        return created
