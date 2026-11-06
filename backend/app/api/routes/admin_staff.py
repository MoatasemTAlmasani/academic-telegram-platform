"""Admin staff management API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.passwords import hash_password
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.identity import Role, StaffProfile, User
from database.models.enums import UserStatus


router = APIRouter(
    prefix="/admin/staff",
    tags=["admin-staff"],
)


class StaffResponse(BaseModel):
    id: UUID
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: str
    specialization: str | None = None
    availability: str | None = None
    is_active: bool
    created_at: object
    updated_at: object


class StaffListResponse(BaseModel):
    items: list[StaffResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StaffCreateRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    specialization: str | None = None
    availability: str | None = None
    is_active: bool = True


class StaffUpdateRequest(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    language: str | None = None
    timezone: str | None = None
    status: UserStatus | None = None
    specialization: str | None = None
    availability: str | None = None
    is_active: bool | None = None
    password: str | None = None


def _to_response(user: User) -> StaffResponse:
    profile = user.staff_profile

    return StaffResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        language=user.language,
        timezone=user.timezone,
        status=str(user.status),
        specialization=profile.specialization if profile else None,
        availability=profile.availability if profile else None,
        is_active=profile.is_active if profile else False,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def _get_staff_role(session: AsyncSession) -> Role:
    result = await session.execute(
        select(Role).where(Role.name == "staff")
    )

    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=500,
            detail="Staff role is not configured.",
        )

    return role


async def _get_staff_user(
    session: AsyncSession,
    user_id: UUID,
) -> User | None:
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.staff_profile),
        )
        .where(User.id == user_id, User.deleted_at.is_(None))
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    if not any(role.name == "staff" for role in user.roles):
        return None

    return user


@router.get(
    "",
    response_model=StaffListResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_READ)),
    ],
)
async def list_staff(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status: str | None = Query(default=None, max_length=32),
) -> StaffListResponse:

    staff_role = await _get_staff_role(session)

    query = (
        select(User)
        .join(User.roles)
        .outerjoin(StaffProfile, StaffProfile.user_id == User.id)
        .options(
            selectinload(User.roles),
            selectinload(User.staff_profile),
        )
        .where(Role.id == staff_role.id, User.deleted_at.is_(None))
        .order_by(User.created_at.desc())
    )

    count_query = (
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(User.roles)
        .where(Role.id == staff_role.id, User.deleted_at.is_(None))
    )

    if search:
        pattern = f"%{search.strip()}%"

        search_filter = or_(
            User.username.ilike(pattern),
            User.email.ilike(pattern),
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            User.phone.ilike(pattern),
            StaffProfile.specialization.ilike(pattern),
        )

        query = query.where(search_filter)
        count_query = count_query.outerjoin(
            StaffProfile,
            StaffProfile.user_id == User.id,
        ).where(search_filter)

    if status:
        query = query.where(User.status == status)
        count_query = count_query.where(User.status == status)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size

    result = await session.execute(
        query.offset(offset).limit(page_size)
    )

    users = result.scalars().unique().all()

    total_pages = (total + page_size - 1) // page_size

    return StaffListResponse(
        items=[_to_response(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{user_id}",
    response_model=StaffResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_READ)),
    ],
)
async def get_staff(
    user_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:

    user = await _get_staff_user(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found.",
        )

    return _to_response(user)


@router.post(
    "",
    response_model=StaffResponse,
    status_code=201,
    dependencies=[
        Depends(require_permission(Permission.USERS_CREATE)),
    ],
)
async def create_staff(
    payload: StaffCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:

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

    staff_role = await _get_staff_role(session)

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        language=payload.language,
        timezone=payload.timezone,
        status=payload.status,
    )

    user.roles.append(staff_role)

    profile = StaffProfile(
        specialization=payload.specialization,
        availability=payload.availability,
        is_active=payload.is_active,
    )

    user.staff_profile = profile

    session.add(user)
    await session.flush()
    now = datetime.now(timezone.utc)
    session.add(AuditLog(
        actor_id=current_user.id,
        action="staff.created",
        resource_type="staff",
        resource_id=user.id,
        description=f"Admin created staff member '{user.username}'.",
        event_metadata={
            "specialization": profile.specialization,
            "is_active": profile.is_active,
        },
        created_at=now,
    ))

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.staff_profile),
        )
        .where(User.id == user.id)
    )

    created_user = result.scalar_one()

    return _to_response(created_user)


@router.patch(
    "/{user_id}",
    response_model=StaffResponse,
    dependencies=[
        Depends(require_permission(Permission.USERS_UPDATE)),
    ],
)
async def update_staff(
    user_id: UUID,
    payload: StaffUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:

    user = await _get_staff_user(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found.",
        )

    data = payload.model_dump(exclude_unset=True)
    before = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "language": user.language,
        "timezone": user.timezone,
        "status": str(user.status),
        "specialization": user.staff_profile.specialization if user.staff_profile else None,
        "availability": user.staff_profile.availability if user.staff_profile else None,
        "is_active": user.staff_profile.is_active if user.staff_profile else None,
    }

    password = data.pop("password", None)
    specialization = data.pop("specialization", None)
    availability = data.pop("availability", None)
    is_active = data.pop("is_active", None)

    if "email" in data and data["email"]:
        duplicate = await session.execute(
            select(User).where(
                User.email == data["email"],
                User.id != user_id,
            )
        )

        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Email already exists.",
            )

    for field, value in data.items():
        setattr(user, field, value)

    if password is not None:
        user.password_hash = hash_password(password)

    profile = user.staff_profile

    if profile is None:
        profile = StaffProfile(user_id=user.id)
        user.staff_profile = profile

    if "specialization" in payload.model_fields_set:
        profile.specialization = specialization

    if "availability" in payload.model_fields_set:
        profile.availability = availability

    if "is_active" in payload.model_fields_set:
        profile.is_active = is_active

    now = datetime.now(timezone.utc)
    after = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "language": user.language,
        "timezone": user.timezone,
        "status": str(user.status),
        "specialization": profile.specialization,
        "availability": profile.availability,
        "is_active": profile.is_active,
    }
    session.add(AuditLog(
        actor_id=current_user.id,
        action="staff.updated",
        resource_type="staff",
        resource_id=user.id,
        description=f"Admin updated staff member '{user.username or user.id}'.",
        event_metadata={"before": before, "after": after, "password_changed": password is not None},
        created_at=now,
    ))

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.staff_profile),
        )
        .where(User.id == user.id)
    )

    updated_user = result.scalar_one()

    return _to_response(updated_user)


@router.delete(
    "/{user_id}",
    status_code=204,
    dependencies=[Depends(require_permission(Permission.USERS_DELETE))],
)
async def archive_staff(
    user_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Soft-delete a staff identity and deactivate its profile."""
    user = await _get_staff_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Staff member not found.")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot archive your own account.")

    now = datetime.now(timezone.utc)
    username = user.username or str(user.id)
    user.deleted_at = now
    user.status = UserStatus.SUSPENDED
    if user.staff_profile is not None:
        user.staff_profile.is_active = False

    session.add(AuditLog(
        actor_id=current_user.id,
        action="staff.archived",
        resource_type="staff",
        resource_id=user.id,
        description=f"Admin archived staff member '{username}'.",
        event_metadata={"user_id": str(user.id)},
        created_at=now,
    ))
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return Response(status_code=204)
