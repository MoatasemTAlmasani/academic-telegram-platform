"""Application liveness and readiness endpoints."""

import asyncio
import logging
from typing import Literal, TypedDict

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text

from backend.app.core.config import get_settings
from database.session import engine

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    success: bool
    status: Literal["ok"]
    service: str
    environment: str


class ReadinessResponse(BaseModel):
    """Response returned by the dependency-aware readiness endpoint."""

    success: bool
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
async def readiness_check(response: Response) -> ReadinessResponse:
    """Check PostgreSQL with a bounded, credential-safe probe."""
    settings = get_settings()
    return await _readiness_response(settings, engine, response)


async def _readiness_response(settings, database_engine, response: Response | None = None):
    """Internal probe kept injectable for tests."""
    database_state: Literal["available", "not_configured", "unavailable"]
    if not settings.database_url:
        database_state = "not_configured"
    else:
        try:
            async with asyncio.timeout(3):
                async with database_engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
            database_state = "available"
        except Exception:
            # Do not log exception text: driver errors can contain connection details.
            logger.warning("Database readiness probe failed.")
            database_state = "unavailable"

    dependencies: DependencyState = {
        "database": database_state,
        "redis": "not_checked" if settings.redis_url else "not_configured",
    }
    ready = database_state == "available"
    if response is not None and not ready:
        response.status_code = 503
    return ReadinessResponse(
        success=ready,
        status="ready" if ready else "degraded",
        dependencies=dependencies,
    )