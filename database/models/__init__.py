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
    UserSession,
    role_permissions,
    user_roles,
)
from database.models.notifications import Notification
from database.models.publishing import PublishingJob, PublishingLog
from database.models.quotes import Quote
from database.models.requests import ServiceRequest
from database.models.security import (
    ExternalIdentity,
    IdentityLinkChallenge,
    LoginAttempt,
)
from database.models.settings import AppSettings
from database.models.telegram import TelegramDestination, TelegramValidationLog
from database.models.telegram_runtime import (
    TelegramConversationState,
    TelegramProcessedUpdate,
)

__all__ = [
    "AppSettings",
    "AuditLog",
    "Base",
    "Campaign",
    "Category",
    "ContentItem",
    "ContentTemplate",
    "FileRecord",
    "Notification",
    "ExternalIdentity",
    "IdentityLinkChallenge",
    "LoginAttempt",
    "Permission",
    "PublishingJob",
    "PublishingLog",
    "Quote",
    "Role",
    "Service",
    "ServiceRequest",
    "StaffProfile",
    "TelegramDestination",
    "TelegramConversationState",
    "TelegramProcessedUpdate",
    "TelegramValidationLog",
    "User",
    "UserSession",
    "campaign_destinations",
    "role_permissions",
    "user_roles",
]