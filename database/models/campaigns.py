"""Campaign and campaign destination models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import CampaignStatus


campaign_destinations = Table(
    "campaign_destinations",
    Base.metadata,
    Column(
        "campaign_id",
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "destination_id",
        Uuid(as_uuid=True),
        ForeignKey("telegram_destinations.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Campaign definition; execution is intentionally deferred."""

    __tablename__ = "campaigns"
    __table_args__ = (Index("ix_campaigns_status", "status"),)

    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status"),
        nullable=False,
        default=CampaignStatus.DRAFT,
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    destinations: Mapped[list[TelegramDestination]] = relationship(
        secondary=campaign_destinations,
    )
    publishing_jobs: Mapped[list[PublishingJob]] = relationship(
        back_populates="campaign",
    )