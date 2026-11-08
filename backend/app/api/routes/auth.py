"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import logging
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, func, or_, select, update
from pydantic import BaseModel, Field

from backend.app.api.auth_dependencies import get_current_user
from backend.app.core.config import get_settings
from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork
from backend.app.modules.authentication.passwords import hash_password, verify_password
from backend.app.modules.authentication.jwt import _get_secret_key
from backend.app.infrastructure.telegram.client import TelegramClient
from backend.app.infrastructure.email.client import email_is_configured, send_email
from database.models.audit import AuditLog
from database.models.identity import User, UserSession
from database.models.security import (
    ExternalIdentity,
    IdentityLinkChallenge,
    PasswordRecoveryAttempt,
    PasswordRecoveryChallenge,
)

from backend.app.modules.authentication.authentication import (
    AuthenticationError,
    AuthenticationService,
)


logger = logging.getLogger(__name__)

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


class UserPreferencesRequest(BaseModel):
    language: Literal["ar", "en"] | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    theme: Literal["light", "dark", "system"] | None = None
    date_format: Literal["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"] | None = None
    notifications_email: bool | None = None
    notifications_telegram: bool | None = None


@router.get("/preferences")
async def get_my_preferences(current_user=Depends(get_current_user)):
    return {
        "language": current_user.language or "ar",
        "timezone": current_user.timezone or "Asia/Aden",
        **(current_user.preferences or {}),
    }


@router.patch("/preferences")
async def update_my_preferences(
    payload: UserPreferencesRequest,
    current_user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    updates = payload.model_dump(exclude_unset=True)
    if "language" in updates:
        current_user.language = updates.pop("language")
    if "timezone" in updates:
        current_user.timezone = updates.pop("timezone")
    preferences = dict(current_user.preferences or {})
    preferences.update(updates)
    current_user.preferences = preferences
    now = datetime.now(timezone.utc)
    uow.session.add(AuditLog(
        actor_id=current_user.id,
        action="user.preferences_updated",
        resource_type="user",
        resource_id=current_user.id,
        description="User updated personal preferences.",
        event_metadata={"fields": sorted(payload.model_fields_set)},
        created_at=now,
    ))
    await uow.session.commit()
    return {
        "language": current_user.language,
        "timezone": current_user.timezone,
        **preferences,
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


class PasswordRecoveryRequest(BaseModel):
    """Request a recovery code without revealing whether an account exists."""

    identifier: str = Field(min_length=1, max_length=320)
    channel: Literal["telegram", "email"] = "telegram"


class PasswordRecoveryVerifyRequest(BaseModel):
    """Verify a Telegram-delivered code and replace the account password."""

    identifier: str = Field(min_length=1, max_length=320)
    code: str = Field(pattern=r"^[0-9]{8}$")
    new_password: str = Field(min_length=12, max_length=500)
    channel: Literal["telegram", "email"] = "telegram"


def _recovery_digest(purpose: str, value: str) -> str:
    key = _get_secret_key().encode("utf-8")
    return hmac.new(key, f"{purpose}:{value}".encode("utf-8"), "sha256").hexdigest()


def _normalized_recovery_identifier(value: str) -> str:
    return value.strip().casefold()


def _is_future_datetime(value: datetime | None, now: datetime) -> bool:
    if value is None:
        return False
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return normalized > now


def _is_expired_datetime(value: datetime | None, now: datetime) -> bool:
    if value is None:
        return False
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return normalized <= now


def _recovery_user_query(identifier: str):
    return select(User).where(
        User.deleted_at.is_(None),
        or_(
            func.lower(User.username) == identifier,
            func.lower(User.email) == identifier,
        ),
    )


@router.post("/password-recovery/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_recovery(
    payload: PasswordRecoveryRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, str]:
    """Send a short-lived code only to an account's pre-verified Telegram identity."""
    now = datetime.now(timezone.utc)
    identifier = _normalized_recovery_identifier(payload.identifier)
    ip_address = request.client.host if request.client else "unknown"
    identifier_key = _recovery_digest("password-recovery-identifier", identifier)
    ip_key = _recovery_digest("password-recovery-ip", ip_address)
    window_start = now - timedelta(hours=1)

    # Keep only a bounded 24-hour window; neither raw identifiers nor IPs are stored.
    await uow.session.execute(
        delete(PasswordRecoveryAttempt).where(
            PasswordRecoveryAttempt.attempted_at < now - timedelta(hours=24)
        )
    )
    await uow.session.execute(
        delete(PasswordRecoveryChallenge).where(
            PasswordRecoveryChallenge.expires_at < now - timedelta(days=30)
        )
    )
    identifier_count = await uow.session.scalar(
        select(func.count(PasswordRecoveryAttempt.id)).where(
            PasswordRecoveryAttempt.identifier_key == identifier_key,
            PasswordRecoveryAttempt.attempted_at >= window_start,
        )
    )
    ip_count = await uow.session.scalar(
        select(func.count(PasswordRecoveryAttempt.id)).where(
            PasswordRecoveryAttempt.ip_key == ip_key,
            PasswordRecoveryAttempt.attempted_at >= window_start,
        )
    )
    if (identifier_count or 0) >= 3 or (ip_count or 0) >= 10:
        await uow.session.commit()
        return {
            "status": "accepted",
            "message": "If an eligible account exists, recovery instructions will be sent to its verified Telegram account.",
        }

    uow.session.add(PasswordRecoveryAttempt(
        identifier_key=identifier_key,
        ip_key=ip_key,
        attempted_at=now,
    ))

    user_result = await uow.session.execute(
        _recovery_user_query(identifier).with_for_update()
    )
    user = user_result.scalar_one_or_none()
    settings = get_settings()
    if (
        user is None
        or str(user.status).upper() != "ACTIVE"
        or _is_future_datetime(user.locked_until, now)
        or _is_expired_datetime(user.account_expires_at, now)
    ):
        await uow.session.commit()
        return {"status": "accepted", "message": "If an eligible account exists, recovery instructions will be sent to its verified recovery channel."}

    if payload.channel == "telegram":
        if user.telegram_user_id is None or settings.telegram_bot_token is None:
            await uow.session.commit()
            return {"status": "accepted", "message": "If an eligible account exists, recovery instructions will be sent to its verified recovery channel."}
        identity_provider = "telegram"
        identity_subject = str(user.telegram_user_id)
    else:
        if not user.email or not email_is_configured(settings):
            await uow.session.commit()
            return {"status": "accepted", "message": "If an eligible account exists, recovery instructions will be sent to its verified recovery channel."}
        identity_provider = "email"
        identity_subject = user.email.strip().casefold()

    identity_result = await uow.session.execute(
        select(ExternalIdentity).where(
            ExternalIdentity.user_id == user.id,
            ExternalIdentity.provider == identity_provider,
            func.lower(ExternalIdentity.subject) == identity_subject,
            ExternalIdentity.verified_at.is_not(None),
        )
    )
    identity = identity_result.scalar_one_or_none()
    if identity is None:
        await uow.session.commit()
        return {"status": "accepted", "message": "If an eligible account exists, recovery instructions will be sent to its verified recovery channel."}
    await uow.session.execute(
        update(PasswordRecoveryChallenge)
        .where(
            PasswordRecoveryChallenge.user_id == user.id,
            PasswordRecoveryChallenge.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    code = f"{secrets.randbelow(100_000_000):08d}"
    challenge = PasswordRecoveryChallenge(
        user_id=user.id,
        token_hash=_recovery_digest(f"password-recovery-code-{payload.channel}", f"{user.id}:{code}"),
        delivery_status="PENDING",
        failed_attempts=0,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    uow.session.add(challenge)
    await uow.session.commit()

    language = (user.language or "ar").lower()
    if language == "en":
        message = (
            "Your EHTERAF password recovery code is:\n"
            f"<code>{code}</code>\n\n"
            "It expires in 10 minutes and can be used once. "
            "Never share this code. If you did not request it, ignore this message."
        )
    else:
        message = (
            "رمز استعادة كلمة المرور لمنصة إحتراف هو:\n"
            f"<code>{code}</code>\n\n"
            "تنتهي صلاحية الرمز خلال 10 دقائق ويُستخدم مرة واحدة. "
            "لا تشاركه مع أي شخص. إذا لم تطلبه فتجاهل هذه الرسالة."
        )

    try:
        telegram = TelegramClient(settings.telegram_bot_token)
        await telegram.send_message(int(identity.subject), message)
    except Exception:
        logger.warning("Password recovery delivery failed through verified Telegram channel.")
        await uow.session.execute(
            update(PasswordRecoveryChallenge)
            .where(PasswordRecoveryChallenge.id == challenge.id)
            .values(delivery_status="FAILED", consumed_at=now)
        )
        await uow.session.commit()
        return {
            "status": "accepted",
            "message": "If an eligible account exists, recovery instructions will be sent to its verified Telegram account.",
        }

    await uow.session.execute(
        update(PasswordRecoveryChallenge)
        .where(PasswordRecoveryChallenge.id == challenge.id)
        .values(delivery_status="SENT", delivered_at=datetime.now(timezone.utc))
    )
    await uow.session.commit()
    return {
        "status": "accepted",
        "message": "If an eligible account exists, recovery instructions will be sent to its verified Telegram account.",
    }


@router.post("/password-recovery/verify")
async def verify_password_recovery(
    payload: PasswordRecoveryVerifyRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int | str | bool]:
    """Consume a verified Telegram recovery code and revoke all existing sessions."""
    now = datetime.now(timezone.utc)
    identifier = _normalized_recovery_identifier(payload.identifier)
    user_result = await uow.session.execute(
        _recovery_user_query(identifier).with_for_update()
    )
    user = user_result.scalar_one_or_none()
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The recovery code is invalid or expired.",
    )
    if (
        user is None
        or str(user.status).upper() != "ACTIVE"
        or _is_future_datetime(user.locked_until, now)
        or _is_expired_datetime(user.account_expires_at, now)
    ):
        raise invalid

    challenge_result = await uow.session.execute(
        select(PasswordRecoveryChallenge)
        .where(
            PasswordRecoveryChallenge.user_id == user.id,
            PasswordRecoveryChallenge.delivery_status == "SENT",
            PasswordRecoveryChallenge.consumed_at.is_(None),
            PasswordRecoveryChallenge.expires_at > now,
        )
        .order_by(PasswordRecoveryChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    challenge = challenge_result.scalar_one_or_none()
    if challenge is None:
        raise invalid

    if challenge.failed_attempts >= 5:
        challenge.consumed_at = now
        await uow.session.commit()
        raise invalid

    expected_hash = _recovery_digest(f"password-recovery-code-{payload.channel}", f"{user.id}:{payload.code}")
    if not hmac.compare_digest(challenge.token_hash, expected_hash):
        challenge.failed_attempts += 1
        if challenge.failed_attempts >= 5:
            challenge.consumed_at = now
        await uow.session.commit()
        raise invalid

    stored_hash = getattr(user, "password_hash", None)
    if stored_hash and verify_password(payload.new_password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The new password must be different from the current password.",
        )

    user.password_hash = hash_password(payload.new_password)
    challenge.consumed_at = now
    revoked = await uow.session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now, revoked_reason="password_recovered")
    )
    revoked_count = revoked.rowcount or 0
    uow.session.add(AuditLog(
        actor_id=user.id,
        action="user.password_recovered",
        resource_type="user",
        resource_id=user.id,
        description="User recovered account access through a verified recovery identity.",
        event_metadata={"channel": payload.channel, "revoked_sessions": revoked_count},
        created_at=now,
    ))
    await uow.session.commit()
    return {
        "status": "password_reset",
        "revoked_sessions": revoked_count,
        "reauthentication_required": True,
    }


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
    locked_user_result = await uow.session.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    locked_user = locked_user_result.scalar_one_or_none()
    if (
        locked_user is None
        or locked_user.deleted_at is not None
        or str(locked_user.status).upper() != "ACTIVE"
    ):
        raise HTTPException(status_code=409, detail="This account cannot link identities.")
    if locked_user.telegram_user_id is not None:
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
    expires_at = now + timedelta(minutes=10)
    challenge = IdentityLinkChallenge(
        user_id=current_user.id,
        provider="telegram",
        token_hash=sha256(link_code.encode("utf-8")).hexdigest(),
        created_at=now,
        expires_at=expires_at,
    )
    uow.session.add(challenge)
    await uow.session.commit()

    return TelegramLinkChallengeResponse(
        link_code=link_code,
        bot_command=f"/link {link_code}",
        expires_at=expires_at,
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
