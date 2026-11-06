"""Authentication API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import update
from pydantic import BaseModel, Field

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork
from backend.app.modules.authentication.passwords import hash_password, verify_password
from database.models.audit import AuditLog
from database.models.identity import UserSession

from backend.app.modules.authentication.authentication import (
    AuthenticationError,
    AuthenticationService,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=500)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TokenResponse:
    """Authenticate a user and return an access token."""
    service = AuthenticationService(uow)

    try:
        token = await service.authenticate(
            payload.username,
            payload.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(
        access_token=token,
    )


@router.get("/me")
async def me(
    current_user=Depends(get_current_user),
):
    """Return the currently authenticated user."""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
    }


class ChangePasswordRequest(BaseModel):
    """Authenticated password change requiring proof of the current password."""

    current_password: str = Field(min_length=1, max_length=500)
    new_password: str = Field(min_length=12, max_length=500)


class ChangePasswordResponse(BaseModel):
    status: str
    revoked_sessions: int
    reauthentication_required: bool


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ChangePasswordResponse:
    """Change the authenticated user's password and revoke every session."""
    stored_hash = getattr(current_user, "password_hash", None)
    if not stored_hash or not verify_password(payload.current_password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if verify_password(payload.new_password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The new password must be different from the current password.",
        )

    now = datetime.now(timezone.utc)
    current_user.password_hash = hash_password(payload.new_password)
    result = await uow.session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=now,
            revoked_reason="password_changed",
        )
    )
    revoked_count = result.rowcount or 0
    uow.session.add(
        AuditLog(
            actor_id=current_user.id,
            action="user.password_changed",
            resource_type="user",
            resource_id=current_user.id,
            description="User changed their password.",
            event_metadata={"revoked_sessions": revoked_count},
            created_at=now,
        )
    )
    await uow.session.commit()
    return ChangePasswordResponse(
        status="password_changed",
        revoked_sessions=revoked_count,
        reauthentication_required=True,
    )
