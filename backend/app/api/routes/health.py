"""Application health endpoints."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["ok"]
    service: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Check API health")
@router.get("/healthz", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    """Return a lightweight liveness response without external dependencies."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )