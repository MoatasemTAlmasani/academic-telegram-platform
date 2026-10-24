"""FastAPI RBAC dependencies."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from backend.app.api.auth_dependencies import get_current_user
from backend.app.modules.authentication.permissions import Permission


def require_permission(
    permission: Permission,
) -> Callable:
    """Create a FastAPI dependency requiring one permission."""

    async def permission_dependency(
        current_user=Depends(get_current_user),
    ):
        roles = getattr(current_user, "roles", None) or []

        for role in roles:
            role_permissions = getattr(role, "permissions", None) or []

            for role_permission in role_permissions:
                if getattr(role_permission, "code", None) == permission.value:
                    return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission.value}",
        )

    return permission_dependency
