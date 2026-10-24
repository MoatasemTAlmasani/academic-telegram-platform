"""Academic service application service."""

from __future__ import annotations

from uuid import UUID

from database.models.catalog import Service

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class AcademicService:
    """Application use cases for the academic service catalog."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(self, service_id: UUID) -> Service | None:
        return await self.uow.services.get_by_id(service_id)

    async def create(self, service: Service) -> Service:
        created = await self.uow.services.add(service)
        await self.uow.commit()
        return created

    async def delete(self, service: Service) -> None:
        await self.uow.services.delete(service)
        await self.uow.commit()
