"""File metadata model; binary content is stored outside the database."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import FileAccessStatus, FileScanStatus


class FileRecord(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Secure file metadata without exposing internal filesystem paths."""

    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_owner_id", "owner_id"),
        Index("ix_files_request_id", "request_id"),
    )

    owner_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    scan_status: Mapped[FileScanStatus] = mapped_column(
        SAEnum(FileScanStatus, name="file_scan_status"),
        nullable=False,
        default=FileScanStatus.PENDING,
    )
    access_status: Mapped[FileAccessStatus] = mapped_column(
        SAEnum(FileAccessStatus, name="file_access_status"),
        nullable=False,
        default=FileAccessStatus.PRIVATE,
    )

    owner: Mapped[User | None] = relationship(
        back_populates="files",
        foreign_keys=[owner_id],
    )
    service_request: Mapped[ServiceRequest | None] = relationship(
        back_populates="files",
    )