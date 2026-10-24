"""RBAC demonstration and authorization routes."""

from fastapi import APIRouter, Depends

from backend.app.api.rbac_dependencies import require_permission
from backend.app.modules.authentication.permissions import Permission


router = APIRouter(
    prefix="/rbac",
    tags=["rbac"],
)


@router.get(
    "/users",
    dependencies=[
        Depends(
            require_permission(
                Permission.USERS_READ,
            )
        )
    ],
)
async def read_users():
    """Protected example endpoint requiring users:read."""
    return {
        "status": "ok",
        "permission": Permission.USERS_READ.value,
    }


@router.get(
    "/admin",
    dependencies=[
        Depends(
            require_permission(
                Permission.ADMIN_ACCESS,
            )
        )
    ],
)
async def admin_access():
    """Protected example endpoint requiring admin:access."""
    return {
        "status": "ok",
        "permission": Permission.ADMIN_ACCESS.value,
    }
