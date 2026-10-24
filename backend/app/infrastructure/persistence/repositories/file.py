"""File repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.files import FileRecord

from .base import BaseRepository


class FileRepository(BaseRepository[FileRecord]):
    """Persistence operations for files."""

    model = FileRecord

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_checksum(
        self,
        checksum: str,
    ) -> FileRecord | None:
        result = await self.session.execute(
            select(FileRecord).where(
                FileRecord.checksum == checksum
            )
        )
        return result.scalar_one_or_none()
