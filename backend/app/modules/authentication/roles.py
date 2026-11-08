"""Canonical application roles and their least-privilege permission sets."""

from __future__ import annotations

from enum import StrEnum

from .permissions import Permission


class RoleName(StrEnum):
    """The six platform roles defined by the project roadmap."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    SUPPORT = "support"
    CUSTOMER = "customer"


ROLE_DESCRIPTIONS: dict[RoleName, str] = {
    RoleName.SUPER_ADMIN: "Full platform control, including role and permission governance.",
    RoleName.ADMIN: "Platform administration and operational management, excluding role governance.",
    RoleName.MANAGER: "Supervises staff and operational workflows across requests and services.",
    RoleName.STAFF: "Performs assigned service, request, file, and quotation work.",
    RoleName.SUPPORT: "Handles customer support and request follow-up with limited access.",
    RoleName.CUSTOMER: "Submits and follows up on personal service requests.",
}


_INTERNAL_ACCESS = {Permission.ADMIN_ACCESS}

ROLE_PERMISSIONS: dict[RoleName, set[Permission]] = {
    RoleName.SUPER_ADMIN: set(Permission),
    RoleName.ADMIN: set(Permission) - {Permission.ROLES_MANAGE},
    RoleName.MANAGER: _INTERNAL_ACCESS | {
        Permission.USERS_READ,
        Permission.SERVICES_READ,
        Permission.SERVICES_UPDATE,
        Permission.REQUESTS_READ,
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
        Permission.CAMPAIGNS_UPDATE,
        Permission.TELEGRAM_READ,
        Permission.AUDIT_READ,
    },
    RoleName.STAFF: _INTERNAL_ACCESS | {
        Permission.USERS_READ,
        Permission.SERVICES_READ,
        Permission.SERVICES_UPDATE,
        Permission.REQUESTS_READ,
        Permission.REQUESTS_UPDATE,
        Permission.FILES_READ,
        Permission.FILES_UPLOAD,
        Permission.QUOTES_READ,
        Permission.QUOTES_CREATE,
        Permission.QUOTES_UPDATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.TELEGRAM_READ,
    },
    RoleName.SUPPORT: _INTERNAL_ACCESS | {
        Permission.USERS_READ,
        Permission.SERVICES_READ,
        Permission.REQUESTS_READ,
        Permission.REQUESTS_UPDATE,
        Permission.FILES_READ,
        Permission.FILES_UPLOAD,
        Permission.QUOTES_READ,
        Permission.TELEGRAM_READ,
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


def permissions_for_role(role_name: str | RoleName) -> set[Permission]:
    """Return a copy of the canonical permission set for a known role."""

    try:
        role = role_name if isinstance(role_name, RoleName) else RoleName(role_name)
    except ValueError:
        return set()
    return set(ROLE_PERMISSIONS[role])
