"""Telegram destination and validation history models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from database.models.enums import (
    TelegramBotStatus,
    TelegramChatType,
    TelegramPrivacyStatus,
    TelegramValidationStatus,
)


class TelegramDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Telegram group/channel record awaiting or having validation."""

    __tablename__ = "telegram_destinations"
    __table_args__ = (
        Index("ix_telegram_destinations_username", "username"),
        Index("ix_telegram_destinations_chat_id", "chat_id"),
        Index("ix_telegram_destinations_validation_status", "validation_status"),
    )

    original_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    normalized_identifier: Mapped[str | None] = mapped_column(
        String(512),
        unique=True,
        nullable=True,
    )
    chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[TelegramChatType] = mapped_column(
        SAEnum(TelegramChatType, name="telegram_chat_type"),
        nullable=False,
        default=TelegramChatType.UNKNOWN,
    )
    privacy_status: Mapped[TelegramPrivacyStatus] = mapped_column(
        SAEnum(TelegramPrivacyStatus, name="telegram_privacy_status"),
        nullable=False,
        default=TelegramPrivacyStatus.UNKNOWN,
    )
    bot_status: Mapped[TelegramBotStatus] = mapped_column(
        SAEnum(TelegramBotStatus, name="telegram_bot_status"),
        nullable=False,
        default=TelegramBotStatus.UNKNOWN,
    )
    can_post: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    validation_status: Mapped[TelegramValidationStatus] = mapped_column(
        SAEnum(TelegramValidationStatus, name="telegram_validation_status"),
        nullable=False,
        default=TelegramValidationStatus.INVALID_LINK,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    validation_logs: Mapped[list[TelegramValidationLog]] = relationship(
        back_populates="destination",
    )


class TelegramValidationLog(UUIDPrimaryKeyMixin, Base):
    """Immutable result history for future Telegram validation attempts."""

    __tablename__ = "telegram_validation_logs"
    __table_args__ = (
        Index("ix_telegram_validation_logs_destination_id", "destination_id"),
        Index("ix_telegram_validation_logs_checked_at", "checked_at"),
    )

    destination_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("telegram_destinations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[TelegramValidationStatus] = mapped_column(
        SAEnum(TelegramValidationStatus, name="telegram_validation_status"),
        nullable=False,
    )
    bot_status: Mapped[TelegramBotStatus] = mapped_column(
        SAEnum(TelegramBotStatus, name="telegram_bot_status"),
        nullable=False,
    )
    can_post: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    destination: Mapped[TelegramDestination] = relationship(
        back_populates="validation_logs",
    )