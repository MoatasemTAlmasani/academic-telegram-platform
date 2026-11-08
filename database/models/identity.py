"""User, role, permission, and staff models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from database.models.enums import UserStatus


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class UserSession(UUIDPrimaryKeyMixin, Base):
    """Server-side session used for access-token revocation."""

    __tablename__ = "user_sessions"

    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index("ix_user_sessions_revoked_at", "revoked_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Platform identity with optional password authentication."""

    __tablename__ = "users"

    telegram_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        String(32),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    account_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
    )
    staff_profile: Mapped[StaffProfile | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    service_requests: Mapped[list[ServiceRequest]] = relationship(
        back_populates="customer",
        foreign_keys="ServiceRequest.customer_id",
    )
    files: Mapped[list[FileRecord]] = relationship(
        back_populates="owner",
        foreign_keys="FileRecord.owner_id",
    )
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
    )


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Named role used by future authorization policies."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list[User]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
    )


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Atomic permission code used by future RBAC checks."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
    )


class StaffProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Staff-specific extension of a user identity."""

    __tablename__ = "staff_profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(back_populates="staff_profile")