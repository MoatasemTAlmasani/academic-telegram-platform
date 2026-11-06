"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import logging
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, func, or_, select, update
from pydantic import BaseModel, Field

from backend.app.api.auth_dependencies import get_current_user
from backend.app.core.config import get_settings
from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork
from backend.app.modules.authentication.passwords import hash_password, verify_password
from backend.app.modules.authentication.jwt import _get_secret_key
from backend.app.infrastructure.telegram.client import TelegramClient
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


class TokenResponse(Bm���jםetail="The new password must be different from the current password.",
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


class PasswordRecoveryVerifyRequest(BaseModel):
    """Verify a Telegram-delivered code and replace the account password."""

    identifier: str = Field(min_length=1, max_length=320)
    code: str = Field(pattern=r"^[0-9]{8}$")
    new_pam���jם     )
    )
    identity = identity_result.scalar_one_or_none()
    if identity is None:
        await uow.session.commit()
        return {
            "status": "accepted",
            "message": "If an eligible account exists, recovery instructions will be sent to its verified Telegram account.",
        }

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
        token_hash=_recovery_digest("password-recovery-code", f"{user.id}:{code}"),
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
            "تنت٭���jם