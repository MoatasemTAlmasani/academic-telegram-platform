"""Service catalog models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Category(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Major service category managed as data, not application constants."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    services: Mapped[list[Service]] = relationship(back_populates="category")


class Service(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Academic or student service listed in the catalog."""

    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_services_category_name"),)

    category_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped[Category] = relationship(back_populates="services")
    service_requests: Mapped[list[ServiceRequest]] = relationship(
        back_populates="service",
    )