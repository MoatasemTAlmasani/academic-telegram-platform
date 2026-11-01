"""Service request model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import RequestPriority, ServiceRequestStatus


class ServiceRequest(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Customer request foundation; workflow transitions come later."""

    __tablename__ = "service_requests"
    __table_args__ = (
        Index("ix_service_requests_customer_id", "customer_id"),
        Index("ix_service_requests_service_id", "service_id"),
        Index("ix_service_requests_status", "status"),
        Index("ix_service_requests_deadline", "deadline"),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ServiceRequestStatus] = mapped_column(
        SAEnum(ServiceRequestStatus, name="service_request_status"),
        nullable=False,
        default=ServiceRequestStatus.NEW,
    )
    telegram_update_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
    )
    priority: Mapped[RequestPriority] = mapped_column(
        SAEnum(RequestPriority, name="request_priority"),
        nullable=False,
        default=RequestPriority.NORMAL,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[User] = relationship(
        back_populates="service_requests",
        foreign_keys=[customer_id],
    )
    service: Mapped[Service] = relationship(back_populates="service_requests")
    files: Mapped[list[FileRecord]] = relationship(back_populates="service_request")
    quotes: Mapped[list[Quote]] = relationship(back_populates="service_request")