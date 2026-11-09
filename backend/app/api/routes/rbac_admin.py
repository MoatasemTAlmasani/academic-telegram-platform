"""RBAC administration API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
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


def _effective_permission_codes(user) -> set[str]:
    """Return the permission union actually assigned to an authenticated user."""

    return {
        permission.code
        for role in (getattr(user, "roles", None) or [])
        for permission in (getattr(role, "permissions", None) or [])
        if getattr(permission, "code", None)
    }


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


class RBACOverviewResponse(BaseModel):
    total_roles: int
    system_roles: int
    custom_roles: int
    active_roles: int | None = None
    inactive_roles: int | None = None
    role_status_supported: bool
    permission_catalog_size: int
    users_with_roles: int
    recent_rbac_changes: int
    recent_change_window_days: int


class RBACRoleCreateRequest(BaseModel):
    """Validated input for creating a non-system custom role."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RBACRoleCreateResponse(BaseModel):
    role: RBACRoleResponse


class RBACRoleUpdateRequest(BaseModel):
    """Partial metadata update for an existing custom role."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RBACRoleUpdateResponse(BaseModel):
    role: RBACRoleResponse


class RBACRolePermissionUpdateRequest(BaseModel):
    permission_codes: list[str]


class RBACRolePermissionUpdateResponse(BaseModel):
    role: RBACRoleResponse


@router.get(
    "/overview",
    response_model=RBACOverviewResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def get_rbac_overview(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return only database-backed RBAC counts; role lifecycle status is not modeled."""

    canonical_names = (
        "super_admin",
        "admin",
        "manager",
        "staff",
        "support",
        "customer",
    )
    window_days = 30
    since = datetime.now(timezone.utc) - timedelta(days=window_days)

    total_roles = await session.execute(select(func.count(Role.id)))
    system_roles = await session.execute(
        select(func.count(Role.id)).where(Role.name.in_(canonical_names))
    )
    permission_count = await session.execute(
        select(func.count(PermissionModel.id))
    )
    users_with_roles = await session.execute(
        select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.roles.any(),
        )
    )
    recent_changes = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.action.in_(
                (
                    "rbac.role_created",
                    "rbac.role_updated",
                    "rbac.role_duplicated",
                    "rbac.role_permissions_updated",
                    "user.role_assigned",
                    "user.roles_assigned",
                )
            ),
            AuditLog.created_at >= since,
        )
    )

    total = int(total_roles.scalar_one() or 0)
    system = int(system_roles.scalar_one() or 0)
    return RBACOverviewResponse(
        total_roles=total,
        system_roles=system,
        custom_roles=max(0, total - system),
        active_roles=None,
        inactive_roles=None,
        role_status_supported=False,
        permission_catalog_size=int(permission_count.scalar_one() or 0),
        users_with_roles=int(users_with_roles.scalar_one() or 0),
        recent_rbac_changes=int(recent_changes.scalar_one() or 0),
        recent_change_window_days=window_days,
    )


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


@router.post(
    "/roles",
    response_model=RBACRoleCreateResponse,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))],
)
async def create_custom_role(
    payload: RBACRoleCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a custom role without changing canonical system roles."""

    canonical_names = {
        "super_admin",
        "admin",
        "manager",
        "staff",
        "support",
        "customer",
    }
    if payload.name in canonical_names:
        raise HTTPException(
            status_code=409,
            detail="Canonical system role names are reserved.",
        )

    existing = await session.execute(
        select(Role).where(func.lower(Role.name) == payload.name).with_for_update()
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A role with this name already exists.")

    role = Role(name=payload.name, description=payload.description)
    session.add(role)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A role with this name already exists.",
        ) from exc

    now = datetime.now(timezone.utc)
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="rbac.role_created",
            resource_type="role",
            resource_id=role.id,
            description=f"Created custom role '{role.name}'.",
            event_metadata={
                "role_name": role.name,
                "description": role.description,
                "role_type": "custom",
            },
            created_at=now,
        )
    )
    await session.commit()
    await session.refresh(role)

    return RBACRoleCreateResponse(
        role=RBACRoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[],
        )
    )


@router.post(
    "/roles/{role_id}/duplicate",
    response_model=RBACRoleCreateResponse,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))],
)
async def duplicate_custom_role(
    role_id: UUID,
    payload: RBACRoleCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Duplicate a role into a custom role without copying protected governance."""

    source_result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
        .with_for_update()
    )
    source_role = source_result.scalar_one_or_none()
    if source_role is None:
        raise HTTPException(status_code=404, detail="Source role not found.")
    if source_role.name == "super_admin":
        raise HTTPException(
            status_code=409,
            detail="The Super Admin role cannot be duplicated.",
        )

    canonical_names = {
        "super_admin",
        "admin",
        "manager",
        "staff",
        "support",
        "customer",
    }
    if payload.name in canonical_names:
        raise HTTPException(
            status_code=409,
            detail="Canonical system role names are reserved.",
        )

    duplicate = await session.execute(
        select(Role).where(func.lower(Role.name) == payload.name).with_for_update()
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A role with this name already exists.")

    copied_permissions = [
        permission
        for permission in source_role.permissions
        if permission.code != Permission.ROLES_MANAGE.value
    ]
    copied_codes = {permission.code for permission in copied_permissions}
    unauthorized_codes = sorted(
        copied_codes - _effective_permission_codes(current_user)
    )
    if unauthorized_codes:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "You cannot duplicate permissions beyond your own effective access.",
                "unauthorized_permissions": unauthorized_codes,
            },
        )

    new_role = Role(
        name=payload.name,
        description=payload.description or source_role.description,
        permissions=copied_permissions,
    )
    session.add(new_role)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A role with this name already exists.",
        ) from exc

    now = datetime.now(timezone.utc)
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="rbac.role_duplicated",
            resource_type="role",
            resource_id=new_role.id,
            description=f"Duplicated role '{source_role.name}' as '{new_role.name}'.",
            event_metadata={
                "source_role_id": str(source_role.id),
                "source_role_name": source_role.name,
                "new_role_name": new_role.name,
                "copied_permission_codes": sorted(copied_codes),
                "excluded_permission_codes": (
                    [Permission.ROLES_MANAGE.value]
                    if any(
                        permission.code == Permission.ROLES_MANAGE.value
                        for permission in source_role.permissions
                    )
                    else []
                ),
            },
            created_at=now,
        )
    )
    await session.commit()

    return RBACRoleCreateResponse(
        role=RBACRoleResponse(
            id=new_role.id,
            name=new_role.name,
            description=new_role.description,
            permissions=[
                RBACPermissionResponse(
                    id=permission.id,
                    code=permission.code,
                    description=permission.description,
                )
                for permission in copied_permissions
            ],
        )
    )


@router.patch(
    "/roles/{role_id}",
    response_model=RBACRoleUpdateResponse,
    dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))],
)
async def update_custom_role(
    role_id: UUID,
    payload: RBACRoleUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update the name/description of a custom role without mutating system roles."""

    role_result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
        .with_for_update()
    )
    role = role_result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")

    canonical_names = {
        "super_admin",
        "admin",
        "manager",
        "staff",
        "support",
        "customer",
    }
    if role.name in canonical_names:
        raise HTTPException(
            status_code=409,
            detail="Canonical system roles cannot be edited.",
        )

    if "name" in payload.model_fields_set and payload.name is None:
        raise HTTPException(status_code=422, detail="Role name cannot be null.")

    before = {"name": role.name, "description": role.description}
    next_name = payload.name if "name" in payload.model_fields_set else role.name
    next_description = (
        payload.description
        if "description" in payload.model_fields_set
        else role.description
    )

    if next_name in canonical_names:
        raise HTTPException(
            status_code=409,
            detail="Canonical system role names are reserved.",
        )

    if next_name != role.name:
        duplicate = await session.execute(
            select(Role)
            .where(func.lower(Role.name) == next_name, Role.id != role.id)
            .with_for_update()
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="A role with this name already exists.",
            )

    after = {"name": next_name, "description": next_description}
    if before != after:
        role.name = next_name
        role.description = next_description
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="A role with this name already exists.",
            ) from exc

        now = datetime.now(timezone.utc)
        session.add(
            AuditLog(
                actor_id=current_user.id,
                action="rbac.role_updated",
                resource_type="role",
                resource_id=role.id,
                description=f"Updated custom role '{role.name}'.",
                event_metadata={
                    "before": before,
                    "after": after,
                },
                created_at=now,
            )
        )
        await session.commit()

    refreshed_result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role.id)
    )
    role = refreshed_result.scalar_one()

    return RBACRoleUpdateResponse(
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

    # A grantor may only delegate permissions already present in their own
    # effective access. This remains enforced even if roles:manage is misassigned.
    actor_permissions = _effective_permission_codes(current_user)
    unauthorized_codes = sorted(requested_codes - actor_permissions)
    if unauthorized_codes:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "You cannot grant permissions beyond your own effective access.",
                "unauthorized_permissions": unauthorized_codes,
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
