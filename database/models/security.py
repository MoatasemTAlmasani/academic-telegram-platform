"""Security-related persistence models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
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


class ExternalIdentity(UUIDPrimaryKeyMixin, Base):
    """Verified external identity linked to one platform account."""

    __tablename__ = "external_identities"

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_external_identity_provider_subject"),
        UniqueConstraint("user_id", "provider", name="uq_external_identity_user_provider"),
        Index("ix_external_identities_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class IdentityLinkChallenge(UUIDPrimaryKeyMixin, Base):
    """Single-use, expiring challenge proving ownership of an external identity."""

    __tablename__ = "identity_link_challenges"

    __table_args__ = (
        Index("ix_identity_link_challenges_user_id", "user_id"),
        Index("ix_identity_link_challenges_expires_at", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordRecoveryAttempt(UUIDPrimaryKeyMixin, Base):
    """Hashed request metadata used to throttle password recovery without storing identifiers or IPs."""

    __tablename__ = "password_recovery_attempts"
    __table_args__ = (
        Index("ix_password_recovery_attempts_identifier_time", "identifier_key", "attempted_at"),
        Index("ix_password_recovery_attempts_ip_time", "ip_key", "attempted_at"),
        Index("ix_password_recovery_attempts_attempted_at", "attempted_at"),
    )

    identifier_key: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PasswordRecoveryChallenge(UUIDPrimaryKeyMixin, Base):
    """Short-lived, single-use password recovery challenge delivered to a verified channel."""

    __tablename__ = "password_recovery_challenges"
    __table_args__ = (
        Index("ix_password_recovery_challenges_user_id", "user_id"),
        Index("ix_password_recovery_challenges_expires_at", "expires_at"),
        Index("ix_password_recovery_challenges_delivery_status", "delivery_status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
