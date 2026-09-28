"""Publishing job and attempt log models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import PublishingStatus


class PublishingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A future queue item connecting content, campaign, and destination."""

    __tablename__ = "publishing_jobs"
    __table_args__ = (
        Index("ix_publishing_jobs_status_scheduled_at", "status", "scheduled_at"),
        Index("ix_publishing_jobs_campaign_id", "campaign_id"),
        Index("ix_publishing_jobs_content_id", "content_id"),
        Index("ix_publishing_jobs_destination_id", "destination_id"),
    )

    campaign_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("content_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destination_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("telegram_destinations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PublishingStatus] = mapped_column(
        SAEnum(PublishingStatus, name="publishing_status"),
        nullable=False,
        default=PublishingStatus.PENDING,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="publishing_jobs")
    publishing_logs: Mapped[list[PublishingLog]] = relationship(
        back_populates="publishing_job",
    )


class PublishingLog(UUIDPrimaryKeyMixin, Base):
    """Immutable log of a future publishing attempt."""

    __tablename__ = "publishing_logs"
    __table_args__ = (
        Index("ix_publishing_logs_job_id", "publishing_job_id"),
        Index("ix_publishing_logs_created_at", "created_at"),
    )

    publishing_job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("publishing_jobs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PublishingStatus] = mapped_column(
        SAEnum(PublishingStatus, name="publishing_status"),
        nullable=False,
    )
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    publishing_job: Mapped[PublishingJob] = relationship(
        back_populates="publishing_logs",
    )