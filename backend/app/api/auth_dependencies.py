"""Authentication dependencies for FastAPI."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.api.dependencies import get_user_service
from backend.app.infrastructure.persistence.database import get_session
from backend.app.application.services.user import UserService
from backend.app.modules.authentication.jwt import decode_access_token_with_session
from database.models.identity import UserSession


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    """Return the authenticated application user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id, session_id = decode_access_token_with_session(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    session_result = await session.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    active_session = session_result.scalar_one_or_none()
    if active_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is unavailable or has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_service.get_by_id(user_id)

    if (
        user is None
        or str(user.status).upper() != "ACTIVE"
        or getattr(user, "deleted_at", None) is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is unavailable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
