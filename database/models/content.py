"""Content and content template models."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Index, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import ContentStatus, ContentType


class ContentItem(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Reusable content record for future campaigns."""

    __tablename__ = "content_items"
    __table_args__ = (
        Index("ix_content_items_status", "status"),
        Index("ix_content_items_created_by", "created_by"),
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    media: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type"),
        nullable=False,
        default=ContentType.TEXT,
    )
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(ContentStatus, name="content_status"),
        nullable=False,
        default=ContentStatus.DRAFT,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class ContentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Named content template foundation."""

    __tablename__ = "content_templates"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type"),
        nullable=False,
        default=ContentType.TEXT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )