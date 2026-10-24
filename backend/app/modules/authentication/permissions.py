"""RBAC permission constants."""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    """Application permissions."""

    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    SERVICES_READ = "services:read"
    SERVICES_CREATE = "services:create"
    SERVICES_UPDATE = "services:update"
    SERVICES_DELETE = "services:delete"

    REQUESTS_READ = "requests:read"
    REQUESTS_CREATE = "requests:create"
    REQUESTS_UPDATE = "requests:update"

    FILES_READ = "files:read"
    FILES_UPLOAD = "files:upload"
    FILES_DELETE = "files:delete"

    QUOTES_READ = "quotes:read"
    QUOTES_CREATE = "quotes:create"
    QUOTES_UPDATE = "quotes:update"

    CONTENT_READ = "content:read"
    CONTENT_CREATE = "content:create"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"

    CAMPAIGNS_READ = "campaigns:read"
    CAMPAIGNS_CREATE = "campaigns:create"
    CAMPAIGNS_UPDATE = "campaigns:update"
    CAMPAIGNS_DELETE = "campaigns:delete"

    TELEGRAM_READ = "telegram:read"
    TELEGRAM_MANAGE = "telegram:manage"

    AUDIT_READ = "audit:read"

    ADMIN_ACCESS = "admin:access"
