"""Security-related persistence models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, UUIDPrimaryKeyMixin


class LoginAttempt(UUIDPrimaryKeyMixin, Base):
    """Privacy-conscious record of a login attempt for throttling and review."""

    __tablename__ = "login_attempts"

    __table_args__ = (
        Index("ix_login_attempts_username_time", "username_key", "attempted_at"),
        Index("ix_login_attempts_ip_time", "ip_address", "attempted_at"),
        Index("ix_login_attempts_attempted_at", "attempted_at"),
    )

    username_key: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
