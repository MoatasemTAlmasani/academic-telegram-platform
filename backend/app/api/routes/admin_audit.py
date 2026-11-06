"""Administrative audit log API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog


router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["admin-audit"],
)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    description: str | None
    event_metadata: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: object


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get(
    "",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_permission(Permission.AUDIT_READ))],
)
async def list_audit_logs(
    action: str | None = Query(default=None, max_length=150),
    search: str | None = Query(default=None, max_length=200),
    resource_type: str | None = Query(default=None, max_length=100),
    actor_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    filters = []

    if action:
        filters.append(AuditLog.action == action.strip())

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                AuditLog.action.ilike(pattern),
                AuditLog.resource_type.ilike(pattern),
                AuditLog.description.ilike(pattern),
            )
        )

    if resource_type:
        filters.append(
            AuditLog.resource_type == resource_type.strip()
        )

    if actor_id:
        filters.append(AuditLog.actor_id == actor_id)

    count_query = select(func.count(AuditLog.id))

    if filters:
        count_query = count_query.where(*filters)

    count_result = await session.execute(count_query)
    total = int(count_result.scalar_one() or 0)

    query = (
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)

    return AuditLogListResponse(
        items=list(result.scalars().all()),
        total=total,
        limit=limit,
        offset=offset,
    )
