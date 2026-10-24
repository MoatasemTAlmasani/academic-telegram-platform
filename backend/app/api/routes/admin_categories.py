"""Admin category management API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.catalog import Category


router = APIRouter(
    prefix="/admin/categories",
    tags=["admin-categories"],
)


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    sort_order: int


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    is_active: bool = True
    sort_order: int = 0


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


@router.get(
    "",
    response_model=list[CategoryResponse],
    dependencies=[Depends(require_permission(Permission.SERVICES_READ))],
)
async def list_categories(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Category)
        .where(Category.deleted_at.is_(None))
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )

    return [
        CategoryResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            is_active=item.is_active,
            sort_order=item.sort_order,
        )
        for item in result.scalars().all()
    ]


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permission(Permission.SERVICES_READ))],
)
async def get_category(
    category_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.deleted_at.is_(None),
        )
    )

    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found.")

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        sort_order=category.sort_order,
    )


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.SERVICES_CREATE))],
)
async def create_category(
    payload: CategoryCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(Category).where(
            Category.name == payload.name,
            Category.deleted_at.is_(None),
        )
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Category with this name already exists.",
        )

    category = Category(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )

    session.add(category)
    await session.commit()
    await session.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        sort_order=category.sort_order,
    )


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permission(Permission.SERVICES_UPDATE))],
)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.deleted_at.is_(None),
        )
    )

    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found.")

    if payload.name is not None and payload.name != category.name:
        duplicate = await session.execute(
            select(Category).where(
                Category.name == payload.name,
                Category.id != category_id,
                Category.deleted_at.is_(None),
            )
        )

        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Category with this name already exists.",
            )

        category.name = payload.name

    if payload.description is not None:
        category.description = payload.description

    if payload.is_active is not None:
        category.is_active = payload.is_active

    if payload.sort_order is not None:
        category.sort_order = payload.sort_order

    await session.commit()
    await session.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        sort_order=category.sort_order,
    )


@router.delete(
    "/{category_id}",
    status_code=204,
    dependencies=[Depends(require_permission(Permission.SERVICES_DELETE))],
)
async def delete_category(
    category_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.deleted_at.is_(None),
        )
    )

    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found.")

    category.deleted_at = category.updated_at
    await session.commit()
