"""Authentication and authorization module."""

from .authentication import AuthenticationError, AuthenticationService
from .authorization import (
    require_permission,
    user_has_permission,
    user_has_role,
)
from .jwt import create_access_token, decode_access_token
from .passwords import hash_password, verify_password
from .permissions import Permission
from .rbac import (
    user_has_all_permissions,
    user_has_any_permission,
)
from .roles import ROLE_PERMISSIONS, RoleName

__all__ = [
    "AuthenticationError",
    "AuthenticationService",
    "Permission",
    "ROLE_PERMISSIONS",
    "RoleName",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "require_permission",
    "user_has_permission",
    "user_has_role",
    "user_has_any_permission",
    "user_has_all_permissions",
]
