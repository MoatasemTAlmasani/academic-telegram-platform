"""Admin services management API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.catalog import Category, Service


router = APIRouter(
    prefix="/admin/services",
    tags=["admin-services"],
)


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    sort_order: int


class ServiceResponse(BaseModel):
    id: UUID
    category_id: UUID
    name: str
    description: str | None = None
    short_description: str | None = None
    is_active: bool
    sort_order: int
    category: CategoryResponse | None = None


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ServiceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID
    name: str = Field(min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=10000)
    short_description: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)


class ServiceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=10000)
    short_description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


def service_response(service: Service) -> ServiceResponse:
    return ServiceResponse(
        id=service.id,
        category_id=service.category_id,
        name=service.name,
        description=service.description,
        short_description=service.short_description,
        is_active=service.is_active,
        sort_order=service.sort_order,
        category=(
            CategoryResponse(
                id=service.category.id,
                name=service.category.name,
                description=service.category.description,
                is_active=service.category.is_active,
                sort_order=service.category.sort_order,
            )
            if service.category
            else None
        ),
    )


@router.get(
    "",
    response_model=ServiceListResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_READ)),
    ],
)
async def list_admin_services(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=255),
    category_id: UUID | None = None,
    is_active: bool | None = None,
):
    query = (
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.deleted_at.is_(None))
        .order_by(Service.created_at.desc())
    )

    count_query = select(func.count(Service.id)).where(Service.deleted_at.is_(None))

    if search:
        pattern = f"%{search.strip()}%"

        condition = or_(
            Service.name.ilike(pattern),
            Service.description.ilike(pattern),
            Service.short_description.ilike(pattern),
        )

        query = query.where(condition)
        count_query = count_query.where(condition)

    if category_id:
        query = query.where(Service.category_id == category_id)
        count_query = count_query.where(Service.category_id == category_id)

    if is_active is not None:
        query = query.where(Service.is_active == is_active)
        count_query = count_query.where(Service.is_active == is_active)

    total = (await session.execute(count_query)).scalar_one()

    result = await session.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )

    services = result.scalars().unique().all()

    return ServiceListResponse(
        items=[service_response(item) for item in services],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )



class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    dependencies=[Depends(require_permission(Permission.SERVICES_READ))],
)
async def list_service_categories(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CategoryListResponse:
    """Return active categories for the admin service form."""

    result = await session.execute(
        select(Category)
        .where(
            Category.is_active.is_(True),
            Category.deleted_at.is_(None),
        )
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )

    categories = result.scalars().all()

    return CategoryListResponse(
        items=[
            CategoryResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
                sort_order=item.sort_order,
            )
            for item in categories
        ]
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_READ)),
    ],
)
async def get_admin_service(
    service_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.id == service_id, Service.deleted_at.is_(None))
    )

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    return service_response(service)


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=201,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_CREATE)),
    ],
)
async def create_admin_service(
    payload: ServiceCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    category = await session.get(Category, payload.category_id)

    if category is None:
        raise HTTPException(
            status_code=400,
            detail="Category not found.",
        )

    existing = await session.execute(
        select(Service).where(
            Service.category_id == payload.category_id,
            Service.name == payload.name,
        )
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Service with this name already exists in the category.",
        )

    service = Service(
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        short_description=payload.short_description,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )

    session.add(service)
    await session.flush()
    now = datetime.now(timezone.utc)
    session.add(AuditLog(
        actor_id=current_user.id,
        action="service.created",
        resource_type="service",
        resource_id=service.id,
        description=f"Admin created service '{service.name}'.",
        event_metadata={
            "category_id": str(service.category_id),
            "is_active": service.is_active,
        },
        created_at=now,
    ))
    await session.commit()

    result = await session.execute(
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.id == service.id)
    )

    return service_response(result.scalar_one())


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_UPDATE)),
    ],
)
async def update_admin_service(
    service_id: UUID,
    payload: ServiceUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.id == service_id, Service.deleted_at.is_(None))
    )

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    before = {
        "category_id": str(service.category_id),
        "name": service.name,
        "description": service.description,
        "short_description": service.short_description,
        "is_active": service.is_active,
        "sort_order": service.sort_order,
    }

    if payload.category_id is not None:
        category = await session.get(Category, payload.category_id)

        if category is None:
            raise HTTPException(
                status_code=400,
                detail="Category not found.",
            )

        service.category_id = payload.category_id

    if payload.name is not None:
        service.name = payload.name

    if payload.description is not None:
        service.description = payload.description

    if payload.short_description is not None:
        service.short_description = payload.short_description

    if payload.is_active is not None:
        service.is_active = payload.is_active

    if payload.sort_order is not None:
        service.sort_order = payload.sort_order

    duplicate = await session.scalar(
        select(Service.id).where(
            Service.category_id == service.category_id,
            Service.name == service.name,
            Service.id != service.id,
            Service.deleted_at.is_(None),
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail="Service with this name already exists in the category.",
        )

    after = {
        "category_id": str(service.category_id),
        "name": service.name,
        "description": service.description,
        "short_description": service.short_description,
        "is_active": service.is_active,
        "sort_order": service.sort_order,
    }
    now = datetime.now(timezone.utc)
    session.add(AuditLog(
        actor_id=current_user.id,
        action="service.updated",
        resource_type="service",
        resource_id=service.id,
        description=f"Admin updated service '{service.name}'.",
        event_metadata={"before": before, "after": after},
        created_at=now,
    ))
    await session.commit()

    result = await session.execute(
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.id == service.id)
    )

    return service_response(result.scalar_one())


@router.delete(
    "/{service_id}",
    status_code=204,
    dependencies=[Depends(require_permission(Permission.SERVICES_DELETE))],
)
async def archive_admin_service(
    service_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Archive a service without destroying request history or foreign keys."""
    service = await session.scalar(
        select(Service).where(
            Service.id == service_id,
            Service.deleted_at.is_(None),
        )
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found.")

    now = datetime.now(timezone.utc)
    service.is_active = False
    service.deleted_at = now
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="service.archived",
            resource_type="service",
            resource_id=service.id,
            description=f"Admin archived service '{service.name}'.",
            event_metadata={"service_id": str(service.id)},
            created_at=now,
        )
    )
    await session.commit()
    return Response(status_code=204)
