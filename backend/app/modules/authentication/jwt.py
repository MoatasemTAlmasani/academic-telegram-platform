"""JWT access-token utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from backend.app.core.config import get_settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _get_secret_key() -> str:
    settings = get_settings()

    if settings.secret_key is None:
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    return settings.secret_key.get_secret_value()


def create_access_token(
    user_id: UUID,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        _get_secret_key(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> UUID:
    """Decode and validate an access token."""
    payload = jwt.decode(
        token,
        _get_secret_key(),
        algorithms=[ALGORITHM],
    )

    if payload.get("type") != "access":
        raise ValueError("Invalid token type.")

    subject = payload.get("sub")

    if not subject:
        raise ValueError("Token subject is missing.")

    try:
        return UUID(subject)
    except ValueError as exc:
        raise ValueError("Invalid token subject.") from exc
