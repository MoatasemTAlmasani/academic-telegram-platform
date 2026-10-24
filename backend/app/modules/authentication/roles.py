"""RBAC role definitions."""

from __future__ import annotations

from enum import StrEnum

from .permissions import Permission


class RoleName(StrEnum):
    """Application roles."""

    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


ROLE_PERMISSIONS: dict[RoleName, set[Permission]] = {
    RoleName.ADMIN: set(Permission),

    RoleName.STAFF: {
        Permission.USERS_READ,
        Permission.SERVICES_READ,
        Permission.SERVICES_UPDATE,
        Permission.REQUESTS_READ,
        Permission.REQUESTS_CREATE,
        Permission.REQUESTS_UPDATE,
        Permission.FILES_READ,
        Permission.FILES_UPLOAD,
        Permission.QUOTES_READ,
        Permission.QUOTES_CREATE,
        Permission.QUOTES_UPDATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.CAMPAIGNS_READ,
        Permission.CAMPAIGNS_CREATE,
        Permission.TELEGRAM_READ,
        Permission.TELEGRAM_MANAGE,
    },

    RoleName.CUSTOMER: {
        Permission.SERVICES_READ,
        Permission.REQUESTS_READ,
        Permission.REQUESTS_CREATE,
        Permission.FILES_READ,
        Permission.FILES_UPLOAD,
        Permission.QUOTES_READ,
        Permission.CONTENT_READ,
        Permission.TELEGRAM_READ,
    },
}
