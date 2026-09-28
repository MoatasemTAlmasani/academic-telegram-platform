"""SQLAlchemy model registry."""

from database.models.audit import AuditLog
from database.models.base import Base
from database.models.campaigns import Campaign, campaign_destinations
from database.models.catalog import Category, Service
from database.models.content import ContentItem, ContentTemplate
from database.models.files import FileRecord
from database.models.identity import (
    Permission,
    Role,
    StaffProfile,
    User,
    role_permissions,
    user_roles,
)
from database.models.notifications import Notification
from database.models.publishing import PublishingJob, PublishingLog
from database.models.quotes import Quote
from database.models.requests import ServiceRequest
from database.models.telegram import TelegramDestination, TelegramValidationLog

__all__ = [
    "AuditLog",
    "Base",
    "Campaign",
    "Category",
    "ContentItem",
    "ContentTemplate",
    "FileRecord",
    "Notification",
    "Permission",
    "PublishingJob",
    "PublishingLog",
    "Quote",
    "Role",
    "Service",
    "ServiceRequest",
    "StaffProfile",
    "TelegramDestination",
    "TelegramValidationLog",
    "User",
    "campaign_destinations",
    "role_permissions",
    "user_roles",
]