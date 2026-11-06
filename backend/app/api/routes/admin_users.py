"""Admin users management API."""

from __future__ import annotations
from datetime import datetime, timezone

from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.identity import Role, User, UserSession
from database.models.audit import AuditLog
from backend.app.modules.authentication.jwt import decode_access_token_with_session

bearer_scheme = HTTPBearer(auto_error=False)


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


def _safe_user_audit_snapshot(user: User) -> dict[str, str | None]:
    """Return approved non-secret account fields for before/after audit metadata."""

    return {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "language": user.language,
        "timezone": user.timezone,
        "status": str(user.status),
    }


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
        normalized_status = status.strip().upper()
        if normalized_status not in {"ACTIVE", "INACTIVE", "SUSPENDED"}:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Unsupported account status.")
        query = query.where(func.upper(User.status) == normalized_status)
        count_query = count_query.where(func.upper(User.status) == normalized_status)

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
        .where(User.id == user_id, User.deleted_at.is_(None))
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

    normalized_username = payload.username.strip()
    normalized_email = payload.email.strip().lower() if payload.email else None
    if len(normalized_username) < 3:
        raise HTTPException(status_code=422, detail="Username must contain at least 3 non-space characters.")

    conditions = [func.lower(User.username) == normalized_username.lower()]

    if normalized_email:
        conditions.append(func.lower(User.email) == normalized_email)

    existing = await session.execute(
        select(User).where(or_(*conditions))
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists.",
        )

    # Role governance belongs to Module 03. Module 02 must not let a user
    # creator assign arbitrary or privileged roles through this endpoint.
    if payload.role.strip().lower() != "customer":
        raise HTTPException(
            status_code=403,
            detail="Role assignment is managed by the Roles & Permissions module.",
        )

    role_result = await session.execute(
        select(Role).where(func.lower(Role.name) == payload.role.strip().lower())
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
        username=normalized_username,
        password_hash=hash_password(payload.password),
        email=normalized_email,
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

    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None or user.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    before_values = _safe_user_audit_snapshot(user)

    if payload.password is not None:
        raise HTTPException(
            status_code=409,
            detail="Password changes must use the secure account recovery workflow.",
        )

    if payload.role is not None:
        raise HTTPException(
            status_code=403,
            detail="Role assignment is managed by the Roles & Permissions module.",
        )

    if payload.username is not None:
        normalized_username = payload.username.strip()
        if len(normalized_username) < 3:
            raise HTTPException(status_code=422, detail="Username must contain at least 3 non-space characters.")
        duplicate = await session.execute(
            select(User).where(
                func.lower(User.username) == normalized_username.lower(),
                User.id != user.id,
            )
        )

        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Username already exists.",
            )

        user.username = normalized_username

    if "email" in payload.model_fields_set:
        normalized_email = payload.email.strip().lower() or None if payload.email else None
        duplicate = await session.execute(
            select(User).where(
                func.lower(User.email) == normalized_email,
                User.id != user.id,
            )
        ) if normalized_email else None

        if duplicate is not None and duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Email already exists.",
            )

        user.email = normalized_email

    if "first_name" in payload.model_fields_set:
        user.first_name = payload.first_name.strip() or None if payload.first_name else None

    if "last_name" in payload.model_fields_set:
        user.last_name = payload.last_name.strip() or None if payload.last_name else None

    if "phone" in payload.model_fields_set:
        user.phone = payload.phone.strip() or None if payload.phone else None

    if "language" in payload.model_fields_set:
        user.language = payload.language.strip() or None if payload.language else None

    if "timezone" in payload.model_fields_set:
        user.timezone = payload.timezone.strip() or None if payload.timezone else None

    if payload.status is not None:
        raise HTTPException(
            status_code=409,
            detail="Account status changes must use the lifecycle action with a reason.",
        )

    audit_log = AuditLog(
        actor_id=current_user.id,
        action="user.updated",
        resource_type="user",
        resource_id=user.id,
        description=f"Admin updated user '{user.username}'.",
        event_metadata={
            "user_id": str(user.id),
            "before": before_values,
            "after": _safe_user_audit_snapshot(user),
        },
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


class AdminUserLifecycleRequest(BaseModel):
    action: Literal["activate", "reactivate", "deactivate", "suspend"]
    reason: str = Field(min_length=5, max_length=500)


class AdminUserLifecycleResponse(BaseModel):
    user_id: UUID
    previous_status: str
    status: str
    revoked_sessions: int


@router.post(
    "/{user_id}/lifecycle",
    response_model=AdminUserLifecycleResponse,
    dependencies=[Depends(require_permission(Permission.USERS_UPDATE))],
)
async def transition_admin_user_lifecycle(
    user_id: UUID,
    payload: AdminUserLifecycleRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdminUserLifecycleResponse:
    """Apply an audited account lifecycle transition and revoke sessions when needed."""
    from fastapi import HTTPException

    result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if len(payload.reason.strip()) < 5:
        raise HTTPException(status_code=422, detail="A meaningful lifecycle reason is required.")

    previous_status = str(user.status).upper()
    transitions = {
        "activate": ({"INACTIVE"}, "ACTIVE"),
        "reactivate": ({"INACTIVE", "SUSPENDED"}, "ACTIVE"),
        "deactivate": ({"ACTIVE"}, "INACTIVE"),
        "suspend": ({"ACTIVE"}, "SUSPENDED"),
    }
    allowed_from, next_status = transitions[payload.action]
    if previous_status not in allowed_from:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot {payload.action} an account in status {previous_status}.",
        )
    if user.id == current_user.id and next_status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate or suspend your own current account.",
        )

    now = datetime.now(timezone.utc)
    user.status = next_status
    revoked_sessions = 0
    if next_status != "ACTIVE":
        revoke_result = await session.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
                revoked_reason=f"account_{payload.action}",
            )
        )
        revoked_sessions = revoke_result.rowcount or 0

    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="user.lifecycle_changed",
            resource_type="user",
            resource_id=user.id,
            description=f"Admin changed account lifecycle for '{user.username}'.",
            event_metadata={
                "user_id": str(user.id),
                "action": payload.action,
                "reason": payload.reason.strip(),
                "before": {"status": previous_status},
                "after": {"status": next_status},
                "revoked_sessions": revoked_sessions,
            },
            created_at=now,
        )
    )
    await session.commit()
    return AdminUserLifecycleResponse(
        user_id=user.id,
        previous_status=previous_status,
        status=next_status,
        revoked_sessions=revoked_sessions,
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
    reason: str = Query(min_length=5, max_length=500),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a platform user from the admin dashboard."""

    from fastapi import HTTPException

    result = await session.execute(
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
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

    if len(reason.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="A meaningful archive reason is required.",
        )

    archived_username = user.username

    # Preserve business references and audit history using the existing soft-delete marker.
    user.status = "INACTIVE"
    user.deleted_at = datetime.now(timezone.utc)
    await session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=datetime.now(timezone.utc),
            revoked_reason="account_archived",
        )
    )

    audit_log = AuditLog(
        actor_id=current_user.id,
        action="user.archived",
        resource_type="user",
        resource_id=user.id,
        description=f"Admin archived user '{archived_username}'.",
        event_metadata={"user_id": str(user.id), "status": "INACTIVE", "reason": reason.strip()},
        created_at=datetime.now(timezone.utc),
    )

    session.add(audit_log)
    await session.commit()


class AdminUserSessionResponse(BaseModel):
    """Safe representation of a user session."""

    id: UUID
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    is_current: bool = False


@router.get(
    "/{user_id}/sessions",
    response_model=list[AdminUserSessionResponse],
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
)
async def list_admin_user_sessions(
    user_id: UUID,
    current_user=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> list[AdminUserSessionResponse]:
    """List recent sessions for an account without exposing token material."""
    from fastapi import HTTPException

    user_result = await session.execute(
        select(User.id).where(User.id == user_id, User.deleted_at.is_(None))
    )
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found.")

    current_session_id = (
        decode_access_token_with_session(credentials.credentials)[1]
        if credentials is not None
        else None
    )
    result = await session.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id)
        .order_by(UserSession.created_at.desc())
        .limit(100)
    )
    sessions = result.scalars().all()
    return [
        AdminUserSessionResponse(
            id=item.id,
            created_at=item.created_at,
            expires_at=item.expires_at,
            last_seen_at=item.last_seen_at,
            revoked_at=item.revoked_at,
            revoked_reason=item.revoked_reason,
            is_current=item.id == current_session_id,
            ip_address=item.ip_address,
            user_agent=item.user_agent,
        )
        for item in sessions
    ]


@router.delete(
    "/{user_id}/sessions/{session_id}",
    status_code=204,
    dependencies=[Depends(require_permission(Permission.USERS_UPDATE))],
)
async def revoke_admin_user_session(
    user_id: UUID,
    session_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke one session belonging to the specified account."""
    from fastapi import HTTPException

    result = await session.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if target.revoked_at is not None:
        return

    now = datetime.now(timezone.utc)
    target.revoked_at = now
    target.revoked_reason = "revoked_by_admin"
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="user.session_revoked",
            resource_type="user_session",
            resource_id=target.id,
            description=f"Admin revoked a session for user '{user_id}'.",
            event_metadata={"user_id": str(user_id), "session_id": str(target.id)},
            created_at=now,
        )
    )
    await session.commit()


@router.post(
    "/{user_id}/sessions/revoke-all",
    response_model=dict[str, int],
    dependencies=[Depends(require_permission(Permission.USERS_UPDATE))],
)
async def revoke_all_admin_user_sessions(
    user_id: UUID,
    current_user=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Revoke every active session belonging to the specified account."""
    from fastapi import HTTPException

    user_result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    now = datetime.now(timezone.utc)
    current_session_id = (
        decode_access_token_with_session(credentials.credentials)[1]
        if credentials is not None
        else None
    )
    revoke_query = update(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > now,
    )
    if user_id == current_user.id and current_session_id is not None:
        revoke_query = revoke_query.where(UserSession.id != current_session_id)
    result = await session.execute(
        revoke_query.values(revoked_at=now, revoked_reason="revoked_all_by_admin")
    )
    revoked_count = result.rowcount or 0
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="user.sessions_revoked_all",
            resource_type="user",
            resource_id=user_id,
            description=f"Admin revoked all active sessions for user '{user_id}'.",
            event_metadata={"user_id": str(user_id), "revoked_count": revoked_count},
            created_at=now,
        )
    )
    await session.commit()
    return {"revoked_count": revoked_count}
