"""Authentication use cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import func, select

from database.models.identity import User, UserSession
from database.models.security import LoginAttempt

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork

from .jwt import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from .passwords import verify_password


class AuthenticationError(Exception):
    """Raised when authentication fails."""


LOGIN_WINDOW_MINUTES = 15
USERNAME_IP_FAILURE_LIMIT = 5
IP_FAILURE_LIMIT = 20
LOGIN_LOCKOUT_MINUTES = 15


class AuthenticationService:
    """Authenticate users, throttle repeated failures, and issue revocable sessions."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """Authenticate a user and return a session-bound access token."""
        now = datetime.now(timezone.utc)
        normalized_username = username.strip().lower()
        username_key = sha256(normalized_username.encode("utf-8")).hexdigest()
        window_start = now - timedelta(minutes=LOGIN_WINDOW_MINUTES)

        pair_count_result = await self.uow.session.execute(
            select(func.count(LoginAttempt.id)).where(
                LoginAttempt.username_key == username_key,
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.succeeded.is_(False),
                LoginAttempt.attempted_at >= window_start,
            )
        )
        pair_failures = pair_count_result.scalar_one()

        ip_failures = 0
        if ip_address:
            ip_count_result = await self.uow.session.execute(
                select(func.count(LoginAttempt.id)).where(
                    LoginAttempt.ip_address == ip_address,
                    LoginAttempt.succeeded.is_(False),
                    LoginAttempt.attempted_at >= window_start,
                )
            )
            ip_failures = ip_count_result.scalar_one()

        if (
            pair_failures >= USERNAME_IP_FAILURE_LIMIT
            or ip_failures >= IP_FAILURE_LIMIT
        ):
            self.uow.session.add(
                LoginAttempt(
                    username_key=username_key,
                    ip_address=ip_address,
                    succeeded=False,
                    attempted_at=now,
                )
            )
            await self.uow.session.commit()
            raise AuthenticationError("Invalid username or password.")

        user = await self.uow.users.get_by_username(normalized_username)
        password_hash = getattr(user, "password_hash", None) if user else None
        account_is_active = (
            user is not None
            and str(user.status).upper() == "ACTIVE"
            and getattr(user, "deleted_at", None) is None
        )

        if (
            not account_is_active
            or not password_hash
            or not verify_password(password, password_hash)
        ):
            self.uow.session.add(
                LoginAttempt(
                    username_key=username_key,
                    ip_address=ip_address,
                    user_id=user.id if user is not None else None,
                    succeeded=False,
                    attempted_at=now,
                )
            )
            await self.uow.session.commit()
            raise AuthenticationError("Invalid username or password.")

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
        self.uow.session.add(
            LoginAttempt(
                username_key=username_key,
                ip_address=ip_address,
                user_id=user.id,
                succeeded=True,
                attempted_at=now,
            )
        )
        token = create_access_token(user.id, session_id)
        await self.uow.session.commit()

        return token
