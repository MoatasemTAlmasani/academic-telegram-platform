"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select, update
from pydantic import BaseModel, Field

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork
from backend.app.modules.authentication.passwords import hash_password, verify_password
from database.models.audit import AuditLog
from database.models.identity import UserSession
from database.models.security import ExternalIdentity, IdentityLinkChallenge

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


class ExternalIdentityResponse(BaseModel):
    provider: str
    subject: str
    display_name: str | None = None
    linked_at: datetime
    verified_at: datetime


class TelegramLinkChallengeResponse(BaseModel):
    provider: Literal["telegram"] = "telegram"
    link_code: str
    bot_command: str
    expires_at: datetime


@router.get(
    "/identity-links",
    response_model=list[ExternalIdentityResponse],
)
async def list_my_identity_links(
    current_user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[ExternalIdentityResponse]:
    """List verified external identities linked to the authenticated account."""
    result = await uow.session.execute(
        select(ExternalIdentity)
        .where(ExternalIdentity.user_id == current_user.id)
        .order_by(ExternalIdentity.linked_at.desc())
    )
    return [
        ExternalIdentityResponse(
            provider=item.provider,
            subject=item.subject,
            display_name=item.display_name,
            linked_at=item.linked_at,
            verified_at=item.verified_at,
        )
        for item in result.scalars().all()
    ]


@router.post(
    "/identity-links/telegram/challenge",
    response_model=TelegramLinkChallengeResponse,
    status_code=201,
)
async def create_telegram_link_challenge(
    current_user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TelegramLinkChallengeResponse:
    """Create a short-lived, single-use code to prove Telegram account ownership."""
    if current_user.telegram_user_id is not None:
        raise HTTPException(
            status_code=409,
            detail="A Telegram account is already linked to this profile.",
        )

    existing_identity = await uow.session.execute(
        select(ExternalIdentity).where(
            ExternalIdentity.user_id == current_user.id,
            ExternalIdentity.provider == "telegram",
        )
    )
    if existing_identity.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="A Telegram identity is already linked to this profile.",
        )

    now = datetime.now(timezone.utc)
    recent_challenge = await uow.session.execute(
        select(IdentityLinkChallenge.id).where(
            IdentityLinkChallenge.user_id == current_user.id,
            IdentityLinkChallenge.provider == "telegram",
            IdentityLinkChallenge.consumed_at.is_(None),
            IdentityLinkChallenge.expires_at > now,
            IdentityLinkChallenge.created_at >= now - timedelta(minutes=1),
        )
    )
    if recent_challenge.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=429,
            detail="A link code was created recently. Wait before requesting another.",
        )

    await uow.session.execute(
        update(IdentityLinkChallenge)
        .where(
            IdentityLinkChallenge.user_id == current_user.id,
            IdentityLinkChallenge.provider == "telegram",
            IdentityLinkChallenge.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    link_code = secrets.token_urlsafe(24)
    challenge = IdentityLinkChallenge(
        user_id=current_user.id,
        provider="telegram",
        token_hash=sha256(link_code.encode("utf-8")).hexdigest(),
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    uow.session.add(challenge)
    await uow.session.commit()

    return TelegramLinkChallengeResponse(
        link_code=link_code,
        bot_command=f"/link {link_code}",
        expires_at=challenge.expires_at,
    )


@router.delete(
    "/identity-links/telegram",
    status_code=204,
)
async def unlink_my_telegram_identity(
    current_user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    """Unlink Telegram only when a password-based sign-in remains available."""
    from fastapi import HTTPException

    if not current_user.password_hash:
        raise HTTPException(
            status_code=409,
            detail="Set a password before unlinking Telegram so you do not lose account access.",
        )

    result = await uow.session.execute(
        select(ExternalIdentity).where(
            ExternalIdentity.user_id == current_user.id,
            ExternalIdentity.provider == "telegram",
        )
    )
    identity = result.scalar_one_or_none()
    if identity is None:
        raise HTTPException(status_code=404, detail="Telegram identity is not linked.")

    now = datetime.now(timezone.utc)
    await uow.session.execute(
        delete(ExternalIdentity).where(ExternalIdentity.id == identity.id)
    )
    current_user.telegram_user_id = None
    uow.session.add(
        AuditLog(
            actor_id=current_user.id,
            action="user.identity_unlinked",
            resource_type="user",
            resource_id=current_user.id,
            description="User unlinked their Telegram identity.",
            event_metadata={"provider": "telegram"},
            created_at=now,
        )
    )
    await uow.session.commit()
