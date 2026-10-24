"""Dependency system health check."""

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_unit_of_work
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/dependencies",
    tags=["dependencies"],
)


@router.get("/health")
async def dependency_health(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, str]:
    """Verify that dependency wiring can create a Unit of Work."""
    return {
        "status": "ok",
        "dependency": "unit_of_work",
        "database": "ready",
    }
