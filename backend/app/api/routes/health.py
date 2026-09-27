"""Application liveness and readiness endpoints."""

from typing import Literal, TypedDict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    success: Literal[True]
    status: Literal["ok"]
    service: str
    environment: str


class ReadinessResponse(BaseModel):
    """Response returned by the dependency-aware readiness endpoint."""

    success: Literal[True]
    status: Literal["ready", "degraded"]
    dependencies: dict[
        str, Literal["available", "not_checked", "not_configured", "unavailable"]
    ]


class DependencyState(TypedDict):
    """Internal representation of a future dependency check."""

    database: Literal["available", "not_checked", "not_configured", "unavailable"]
    redis: Literal["available", "not_checked", "not_configured", "unavailable"]


@router.get("/health", response_model=HealthResponse, summary="Check API health")
@router.get("/healthz", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    """Return a lightweight liveness response without external dependencies."""
    settings = get_settings()
    return HealthResponse(
        success=True,
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Check API readiness",
)
async def readiness_check() -> ReadinessResponse:
    """Report dependency readiness without connecting to services in Phase 1."""
    settings = get_settings()
    dependencies: DependencyState = {
        "database": "not_checked" if settings.database_url else "not_configured",
        "redis": "not_checked" if settings.redis_url else "not_configured",
    }
    status: Literal["ready", "degraded"] = (
        "degraded" if "unavailable" in dependencies.values() else "ready"
    )
    return ReadinessResponse(
        success=True,
        status=status,
        dependencies=dependencies,
    )