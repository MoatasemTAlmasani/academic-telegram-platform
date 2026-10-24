"""Audit application service."""

from __future__ import annotations

from uuid import UUID

from database.models.audit import AuditLog

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class AuditService:
    """Application use cases for audit events."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        audit_id: UUID,
    ) -> AuditLog | None:
        return await self.uow.audit.get_by_id(audit_id)

    async def get_by_actor_id(
        self,
        actor_id: UUID,
    ) -> list[AuditLog]:
        return await self.uow.audit.get_by_actor_id(actor_id)

    async def record(self, audit_log: AuditLog) -> AuditLog:
        created = await self.uow.audit.add(audit_log)
        await self.uow.commit()
        return created
