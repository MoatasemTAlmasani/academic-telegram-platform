"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork
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
