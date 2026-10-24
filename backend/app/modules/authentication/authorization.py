"""Authorization helpers."""

from __future__ import annotations

from database.models.identity import User

from .permissions import Permission
from .roles import ROLE_PERMISSIONS, RoleName


def user_has_permission(
    user: User,
    permission: Permission,
) -> bool:
    """Return whether a user has a requested permission."""
    roles = getattr(user, "roles", None) or []

    for role in roles:
        role_name = getattr(role, "name", None)

        try:
            role_name = RoleName(role_name)
        except (ValueError, TypeError):
            continue

        if permission in ROLE_PERMISSIONS.get(role_name, set()):
            return True

    return False


def user_has_role(
    user: User,
    role_name: RoleName,
) -> bool:
    """Return whether a user has a requested role."""
    roles = getattr(user, "roles", None) or []

    for role in roles:
        if getattr(role, "name", None) == role_name:
            return True

    return False


def require_permission(
    user: User,
    permission: Permission,
) -> None:
    """Raise PermissionError when access is not authorized."""
    if not user_has_permission(user, permission):
        raise PermissionError(
            f"Missing required permission: {permission.value}"
        )
