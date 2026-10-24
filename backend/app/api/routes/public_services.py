"""Public read-only catalog for the academic Mini App."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.infrastructure.persistence.database import get_session
from database.models.catalog import Category, Service

router = APIRouter(prefix="/public/services", tags=["public-services"])


class PublicCategory(BaseModel):
    id: str
    name: str
    description: str | None = None


class PublicService(BaseModel):
    id: str
    category_id: str
    name: str
    description: str | None = None
    short_description: str | None = None
    category: PublicCategory | None = None


class PublicServiceList(BaseModel):
    items: list[PublicService]


@router.get("", response_model=PublicServiceList)
async def list_public_services(
    session: AsyncSession = Depends(get_session),
) -> PublicServiceList:
    result = await session.execute(
        select(Service)
        .join(Category, Service.category_id == Category.id)
        .options(selectinload(Service.category))
        .where(
            Service.is_active.is_(True),
            Service.deleted_at.is_(None),
            Category.is_active.is_(True),
            Category.deleted_at.is_(None),
        )
        .order_by(Service.sort_order.asc(), Service.name.asc())
    )
    services = result.scalars().unique().all()

    return PublicServiceList(
        items=[
            PublicService(
                id=str(service.id),
                category_id=str(service.category_id),
                name=service.name,
                description=service.description,
                short_description=service.short_description,
                category=(
                    PublicCategory(
                        id=str(service.category.id),
                        name=service.category.name,
                        description=service.category.description,
                    )
                    if service.category
                    else None
                ),
            )
            for service in services
        ]
    )
