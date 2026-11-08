"""RBAC administration API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.identity import Role, Permission as PermissionModel


router = APIRouter(
    prefix="/rbac",
    tags=["rbac-management"],
)


class RBACPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str | None = None


class RBACRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    permissions: list[RBACPermissionResponse] = []


class RBACRolePermissionUpdateRequest(BaseModel):
    permission_codes: list[str]


class RBACRolePermissionUpdateResponse(BaseModel):
    role: RBACRoleResponse


@router.get(
    "/roles",
    response_model=list[RBACRoleResponse],
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def list_roles(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all roles with their assigned permissions."""

    result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .order_by(Role.name.asc())
    )

    roles = result.scalars().unique().all()

    return [
        RBACRoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                RBACPermissionResponse(
                    id=permission.id,
                    code=permission.code,
                    description=permission.description,
                )
                for permission in role.permissions
            ],
        )
        for role in roles
    ]


@router.get(
    "/permissions",
    response_model=list[RBACPermissionResponse],
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def list_permissions(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all registered permissions."""

    result = await session.execute(
        select(PermissionModel)
        .order_by(PermissionModel.code.asc())
    )

    permissions = result.scalars().all()

    return [
        RBACPermissionResponse(
            id=permission.id,
            code=permission.code,
            description=permission.description,
        )
        for permission in permissions
    ]


@router.put(
    "/roles/{role_id}/permissions",
    response_model=RBACRolePermissionUpdateResponse,
    dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))],
)
async def update_role_permissions(
    role_id: UUID,
    payload: RBACRolePermissionUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Replace the complete permission set assigned to a role."""

    # Serialize concurrent edits to the same role before reading its permission set.
    role_result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
        .with_for_update()
    )

    role = role_result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found.",
        )

    requested_codes = {
        code.strip()
        for code in payload.permission_codes
        if code and code.strip()
    }

    # The canonical Super Admin role is the root of platform governance.
    if role.name == "super_admin":
        raise HTTPException(
            status_code=409,
            detail="The Super Admin role permissions are protected.",
        )

    # Keep role governance exclusive to the canonical Super Admin role.
    if Permission.ROLES_MANAGE.value in requested_codes:
        raise HTTPException(
            status_code=422,
            detail="The roles:manage permission is reserved for super_admin.",
        )

    if requested_codes:
        permission_result = await session.execute(
            select(PermissionModel).where(
                PermissionModel.code.in_(requested_codes)
            )
        )
        permissions = permission_result.scalars().all()
    else:
        permissions = []

    found_codes = {permission.code for permission in permissions}
    unknown_codes = sorted(requested_codes - found_codes)

    if unknown_codes:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unknown permission codes.",
                "unknown_permissions": unknown_codes,
            },
        )

    before_codes = sorted(permission.code for permission in role.permissions)
    after_codes = sorted(permission.code for permission in permissions)
    if before_codes != after_codes:
        role.permissions = list(permissions)
        now = datetime.now(timezone.utc)
        session.add(
            AuditLog(
                actor_id=current_user.id,
                action="rbac.role_permissions_updated",
                resource_type="role",
                resource_id=role.id,
                description=f"Updated permissions for role '{role.name}'.",
                event_metadata={
                    "role_name": role.name,
                    "before": before_codes,
                    "after": after_codes,
                },
                created_at=now,
            )
        )
        await session.commit()
        await session.refresh(role)

    result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role.id)
    )

    role = result.scalar_one()

    return RBACRolePermissionUpdateResponse(
        role=RBACRoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                RBACPermissionResponse(
                    id=permission.id,
                    code=permission.code,
                    description=permission.description,
                )
                for permission in role.permissions
            ],
        )
    )
