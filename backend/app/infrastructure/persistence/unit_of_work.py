"""Unit of Work for transactional persistence."""

from sqlalchemy.ext.asyncio import AsyncSession

from .repositories.audit import AuditRepository
from .repositories.campaign import CampaignRepository
from .repositories.content import (
    ContentRepository,
    ContentTemplateRepository,
)
from .repositories.file import FileRepository
from .repositories.notification import NotificationRepository
from .repositories.quote import QuoteRepository
from .repositories.request import ServiceRequestRepository
from .repositories.service import ServiceRepository
from .repositories.telegram import TelegramDestinationRepository
from .repositories.user import UserRepository


class UnitOfWork:
    """Coordinate repositories in one database transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

        self.users = UserRepository(session)
        self.services = ServiceRepository(session)
        self.requests = ServiceRequestRepository(session)
        self.files = FileRepository(session)
        self.quotes = QuoteRepository(session)
        self.content = ContentRepository(session)
        self.content_templates = ContentTemplateRepository(session)
        self.campaigns = CampaignRepository(session)
        self.telegram_destinations = TelegramDestinationRepository(session)
        self.notifications = NotificationRepository(session)
        self.audit = AuditRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
