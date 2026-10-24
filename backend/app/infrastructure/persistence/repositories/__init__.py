"""Persistence repositories."""

from .audit import AuditRepository
from .campaign import CampaignRepository
from .content import ContentRepository, ContentTemplateRepository
from .file import FileRepository
from .notification import NotificationRepository
from .quote import QuoteRepository
from .request import ServiceRequestRepository
from .service import ServiceRepository
from .telegram import TelegramDestinationRepository
from .user import UserRepository

__all__ = [
    "AuditRepository",
    "CampaignRepository",
    "ContentRepository",
    "ContentTemplateRepository",
    "FileRepository",
    "NotificationRepository",
    "QuoteRepository",
    "ServiceRequestRepository",
    "ServiceRepository",
    "TelegramDestinationRepository",
    "UserRepository",
]
