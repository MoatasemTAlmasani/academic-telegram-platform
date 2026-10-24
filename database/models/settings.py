"""Application settings persistence model."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, TimestampMixin


class AppSettings(TimestampMixin, Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    app_name: Mapped[str] = mapped_column(
        String(150), nullable=False, default="Academic Services Platform"
    )
    app_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="development"
    )
    default_language: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en"
    )
    default_timezone: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Asia/Aden"
    )
    support_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    support_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
