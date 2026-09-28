"""Quotation model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import QuoteStatus


class Quote(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Quote foundation; payment processing is intentionally out of scope."""

    __tablename__ = "quotes"
    __table_args__ = (
        Index("ix_quotes_request_id", "request_id"),
        Index("ix_quotes_status", "status"),
    )

    request_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quote_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[QuoteStatus] = mapped_column(
        SAEnum(QuoteStatus, name="quote_status"),
        nullable=False,
        default=QuoteStatus.DRAFT,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service_request: Mapped[ServiceRequest] = relationship(back_populates="quotes")