"""Admin users management API."""

from __future__ import annotations
from datetime import datetime, timezone

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.identity import Role, User
from database.models.audit import AuditLog


router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
)


class AdminUserRoleResponse(BaseModel):
    """Role returned in the admin users list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class AdminUserResponse(BaseModel):
    """Safe public representation of an administrative user."""

    id: UUID
    telegram_user_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: str
    roles: list[AdminUserRoleResponse]
    created_at: object
    updated_at: object


class AdminUserListResponse(BaseModel):
    """Paginated users response."""

    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get(
    "",
    response_model=AdminUserListResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_READ)),
    ],
)
async def list_admin_users(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status: str | None = Query(default=None, max_length=32),
    role: str | None = Query(default=None, max_length=100),
) -> AdminUserListResponse:
    """List platform users for the admin dashboard."""

    query = (
        select(User)
        .where(User.deleted_at.is_(None))
        .options(selectinload(User.roles))
        .order_by(User.created_at.desc())
    )

    count_query = select(func.count(func.distinct(User.id))).where(
        User.deleted_at.is_(None)
    )

    if search:
        pattern = f"%{search.strip()}%"

        search_filter = or_(
            User.username.ilike(pattern),
            User.email.ilike(pattern),
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            User.phone.ilike(pattern),
        )

        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if status:
        query = query.where(User.status == status)
        count_query = count_query.where(User.status == status)

    if role:
        query = query.join(User.roles).where(Role.name == role)
        count_query = count_query.join(User.roles).where(Role.name == role)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size

    result = await session.execute(
        query.offset(offset).limit(page_size)
    )

    users = result.scalars().unique().all()

    total_pages = (total + page_size - 1) // page_size

    items = [
        AdminUserResponse(
            id=user.id,
            telegram_user_id=user.telegram_user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            language=user.language,
            timezone=user.timezone,
            status=str(user.status),
            roles=[
                AdminUserRoleResponse(
                    id=item.id,
                    name=str(item.name),
                    description=item.description,
                )
                for item in user.roles
            ],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{user_id}",
    response_model=AdminUserResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_READ)),
    ],
)
async def get_admin_user(
    user_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdminUserResponse:
    """Get a single platform user for the admin dashboard."""

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        .where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return AdminUserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        email=user.email,
        language=user.language,
        timezone=user.timezone,
        status=str(user.status),
        roles=[
            AdminUserRoleResponse(
                id=item.id,
                name=str(item.name),
                description=item.description,
            )
            for item in user.roles
        ],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

class AdminUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=12, max_length=500)
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: str = "active"
    role: str = "customer"


@router.post(
    "",
    response_model=AdminUserResponse,
    status_code=201,
    dependencies=[
        Depends(require_permission(Permission.USERS_CREATE)),
    ],
)
async def create_admin_user(
    payload: AdminUserCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdminUserResponse:
    """Create a platform user from the admin dashboard."""

    from fastapi import HTTPException
    from backend.app.modules.authentication.passwords import hash_password

    conditions = [User.username == payload.username]

    if payload.email:
        conditions.append(User.email == payload.email)

    existing = await session.execute(
        select(User).where(or_(*conditions))
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists.",
        )

    role_result = await session.execute(
        select(Role).where(Role.name == payload.role)
    )

    role = role_result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{payload.role}' does not exist.",
        )

    if payload.status.upper() not in {"ACTIVE", "INACTIVE", "SUSPENDED"}:
        raise HTTPException(status_code=422, detail="Unsupported account status.")

    user = User(
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        language=payload.language,
        timezone=payload.timezone,
        status=payload.status.upper(),
    )

    user.roles.append(role)

    session.add(user)
    await session.flush()

    audit_log = AuditLog(
        actor_id=current_user.id,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        description=f"Admin created user '{user.username}'.",
        event_metadata={"role": payload.role},
        created_at=user.created_at,
    )
    session.add(audit_log)
    await session.commit()

    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )

    created_user = result.scalar_one()

    return AdminUserResponse(
        id=created_user.id,
        telegram_user_id=created_user.telegram_user_id,
        username=created_user.username,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        phone=created_user.phone,
        email=created_user.email,
        language=created_user.language,
        timezone=created_user.timezone,
        status=str(created_user.status),
        roles=[
            AdminUserRoleResponse(
                id=item.id,
                name=str(item.name),
                description=item.description,
            )
            for item in created_user.roles
        ],
        created_at=created_user.created_at,
        updated_at=created_user.updated_at,
    )


class AdminUserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=150)
    password: str | None = Field(default=None, min_length=12, max_length=500)
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: str | None = None
    role: str | None = None


@router.patch(
    "/{user_id}",
    response_model=AdminUserResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_UPDATE)),
    ],
)
async def update_admin_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdminUserResponse:
    """Update a platform user from the admin dashboard."""

    from fastapi import HTTPException
    from backend.app.modules.authentication.passwords import hash_password

    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if payload.username is not None and payload.username != user.username:
        duplicate = await session.execute(
            select(User).where(
                User.username == payload.username,
                User.id != user.id,
            )
        )

        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Username already exists.",
            )

        user.username = payload.username

    if payload.email is not None and payload.email != user.email:
        duplicate = await session.execute(
            select(User).where(
                User.email == payload.email,
                User.id != user.id,
            )
        )

        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Email already exists.",
            )

        user.email = payload.email

    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    if payload.first_name is not None:
        user.first_name = payload.first_name

    if payload.last_name is not None:
        user.last_name = payload.last_name

    if payload.phone is not None:
        user.phone = payload.phone

    if payload.language is not None:
        user.language = payload.language

    if payload.timezone is not None:
        user.timezone = payload.timezone

    if payload.status is not None:
        normalized_status = payload.status.upper()
        if normalized_status not in {"ACTIVE", "INACTIVE", "SUSPENDED"}:
            raise HTTPException(status_code=422, detail="Unsupported account status.")
        user.status = normalized_status

    if payload.role is not None:
        role_result = await session.execute(
            select(Role).where(Role.name == payload.role)
        )

        role = role_result.scalar_one_or_none()

        if role is None:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{payload.role}' does not exist.",
            )

        user.roles.clear()
        user.roles.append(role)

    audit_log = AuditLog(
        actor_id=current_user.id,
        action="user.updated",
        resource_type="user",
        resource_id=user.id,
        description=f"Admin updated user '{user.username}'.",
        event_metadata={"user_id": str(user.id)},
        created_at=datetime.now(timezone.utc),
    )
    session.add(audit_log)
    await session.commit()

    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )

    updated_user = result.scalar_one()

    return AdminUserResponse(
        id=updated_user.id,
        telegram_user_id=updated_user.telegram_user_id,
        username=updated_user.username,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        phone=updated_user.phone,
        email=updated_user.email,
        language=updated_user.language,
        timezone=updated_user.timezone,
        status=str(updated_user.status),
        roles=[
            AdminUserRoleResponse(
                id=item.id,
                name=str(item.name),
                description=item.description,
            )
            for item in updated_user.roles
        ],
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
    )


@router.delete(
    "/{user_id}",
    status_code=204,
    dependencies=[
        Depends(require_permission(Permission.USERS_DELETE)),
    ],
)
async def delete_admin_user(
    user_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a platform user from the admin dashboard."""

    from fastapi import HTTPException

    result = await session.execute(
        select(User)
        .where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account.",
        )

    archived_username = user.username

    # Preserve business references and audit history using the existing soft-delete marker.
    user.status = "INACTIVE"
    user.deleted_at = datetime.now(timezone.utc)

    audit_log = AuditLog(
        actor_id=current_user.id,
        action="user.archived",
        resource_type="user",
        resource_id=user.id,
        description=f"Admin archived user '{archived_username}'.",
        event_metadata={"user_id": str(user.id), "status": "INACTIVE"},
        created_at=datetime.now(timezone.utc),
    )

    session.add(audit_log)
    await session.commit()
