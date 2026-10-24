"""File application service."""

from __future__ import annotations

from uuid import UUID

from database.models.files import FileRecord

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class FileService:
    """Application use cases for file records."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        file_id: UUID,
    ) -> FileRecord | None:
        return await self.uow.files.get_by_id(file_id)

    async def get_by_checksum(
        self,
        checksum: str,
    ) -> FileRecord | None:
        return await self.uow.files.get_by_checksum(checksum)

    async def create(self, file_record: FileRecord) -> FileRecord:
        created = await self.uow.files.add(file_record)
        await self.uow.commit()
        return created
