"""Authentication use cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from database.models.identity import User, UserSession

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork

from .jwt import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from .passwords import verify_password


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthenticationService:
    """Authenticate users and issue access tokens."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """Authenticate by username and return an access token."""
        user = await self.uow.users.get_by_username(username)

        if user is None:
            raise AuthenticationError(
                "Invalid username or password."
            )

        # Disabled, suspended, locked, expired, or soft-deleted accounts
        # must never receive a fresh access token.
        if (
            str(user.status).upper() != "ACTIVE"
            or getattr(user, "deleted_at", None) is not None
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )

        password_hash = getattr(user, "password_hash", None)

        if not password_hash or not verify_password(
            password,
            password_hash,
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )

        now = datetime.now(timezone.utc)
        session_id = uuid4()
        session = UserSession(
            id=session_id,
            user_id=user.id,
            created_at=now,
            expires_at=now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=(user_agent[:500] if user_agent else None),
        )
        self.uow.session.add(session)
        token = create_access_token(user.id, session_id)
        await self.uow.session.commit()

        return token
