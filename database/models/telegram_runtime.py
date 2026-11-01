"""Durable state used by the single Telegram polling worker."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class TelegramConversationState(Base):
    """Persist the active conversation state for a Telegram chat."""

    __tablename__ = "telegram_conversation_states"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TelegramProcessedUpdate(Base):
    """Record completed Telegram updates to make polling restart-safe."""

    __tablename__ = "telegram_processed_updates"

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    update_type: Mapped[str] = mapped_column(String(80), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
