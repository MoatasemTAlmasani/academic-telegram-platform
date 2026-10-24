"""Database-backed RBAC authorization."""

from __future__ import annotations

from database.models.identity import User

from .permissions import Permission


def user_has_permission(
    user: User,
    permission: Permission,
) -> bool:
    """Check whether a database-backed user has a permission."""
    roles = getattr(user, "roles", None) or []

    for role in roles:
        permissions = getattr(role, "permissions", None) or []

        for role_permission in permissions:
            permission_name = getattr(role_permission, "code", None)

            if permission_name == permission.value:
                return True

    return False


def user_has_any_permission(
    user: User,
    permissions: set[Permission],
) -> bool:
    """Check whether the user has at least one requested permission."""
    return any(
        user_has_permission(user, permission)
        for permission in permissions
    )


def user_has_all_permissions(
    user: User,
    permissions: set[Permission],
) -> bool:
    """Check whether the user has all requested permissions."""
    return all(
        user_has_permission(user, permission)
        for permission in permissions
    )


def require_permission(
    user: User,
    permission: Permission,
) -> None:
    """Raise PermissionError when permission is missing."""
    if not user_has_permission(user, permission):
        raise PermissionError(
            f"Missing required permission: {permission.value}"
        )
