"""Customer-facing service request endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.infrastructure.persistence.database import get_session
from database.models.catalog import Category, Service
from database.models.enums import UserStatus
from database.models.requests import ServiceRequest


router = APIRouter(
    prefix="/customer/requests",
    tags=["customer-requests"],
)


class CustomerRequestCreate(BaseModel):
    service_id: UUID
    description: str = Field(min_length=3, max_length=10000)
    title: str | None = Field(default=None, min_length=3, max_length=300)
    specialization: str | None = Field(default=None, max_length=255)
    deadline: datetime | None = None


class CustomerRequestItem(BaseModel):
    id: str
    service_id: str
    service_name: str
    title: str
    description: str | None
    status: str
    created_at: datetime
    deadline: datetime | None


class CustomerRequestList(BaseModel):
    items: list[CustomerRequestItem]


async def _require_active_customer(current_user) -> None:
    """Reject inactive, deleted, or non-customer accounts."""
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not available.",
        )

    if str(current_user.status).upper() != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    role_names = {
        str(role.name).lower()
        for role in current_user.roles
    }
    if "customer" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required.",
        )


@router.post(
    "",
    response_model=CustomerRequestItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_request(
    payload: CustomerRequestCreate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CustomerRequestItem:
    """Create a request for the authenticated customer."""
    await _require_active_customer(current_user)

    description = payload.description.strip()
    if len(description) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide more details about your request.",
        )

    result = await session.execute(
        select(Service)
        .join(Category, Service.category_id == Category.id)
        .where(
            Service.id == payload.service_id,
            Service.is_active.is_(True),
            Service.deleted_at.is_(None),
            Category.is_active.is_(True),
            Category.deleted_at.is_(None),
        )
    )
    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected service is unavailable.",
        )

    request_item = ServiceRequest(
        customer_id=current_user.id,
        service_id=service.id,
        title=(payload.title.strip() if payload.title else service.name),
        description=description,
        specialization=payload.specialization,
        deadline=payload.deadline,
    )

    session.add(request_item)
    try:
        await session.commit()
        await session.refresh(request_item)
    except Exception:
        await session.rollback()
        raise

    return CustomerRequestItem(
        id=str(request_item.id),
        service_id=str(service.id),
        service_name=service.name,
        title=request_item.title,
        description=request_item.description,
        status=str(request_item.status),
        created_at=request_item.created_at,
        deadline=request_item.deadline,
    )


@router.get("", response_model=CustomerRequestList)
async def list_customer_requests(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CustomerRequestList:
    """List only non-deleted requests belonging to the authenticated customer."""
    await _require_active_customer(current_user)

    result = await session.execute(
        select(ServiceRequest, Service.name)
        .join(Service, ServiceRequest.service_id == Service.id)
        .where(
            ServiceRequest.customer_id == current_user.id,
            ServiceRequest.deleted_at.is_(None),
        )
        .order_by(ServiceRequest.created_at.desc())
    )

    items = [
        CustomerRequestItem(
            id=str(request_item.id),
            service_id=str(request_item.service_id),
            service_name=service_name,
            title=request_item.title,
            description=request_item.description,
            status=str(request_item.status),
            created_at=request_item.created_at,
            deadline=request_item.deadline,
        )
        for request_item, service_name in result.all()
    ]

    return CustomerRequestList(items=items)
