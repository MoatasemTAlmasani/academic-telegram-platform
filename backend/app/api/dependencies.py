"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.audit import AuditService
from backend.app.application.services.campaign import CampaignService
from backend.app.application.services.content import ContentService
from backend.app.application.services.file import FileService
from backend.app.application.services.notification import NotificationService
from backend.app.application.services.quote import QuoteService
from backend.app.application.services.request import ServiceRequestService
from backend.app.application.services.service import AcademicService
from backend.app.application.services.telegram import TelegramService
from backend.app.application.services.user import UserService
from backend.app.infrastructure.persistence.database import get_session
from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


async def get_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session to a request."""
    yield session


def get_unit_of_work(
    session: AsyncSession = Depends(get_db),
) -> UnitOfWork:
    """Provide a Unit of Work for a request."""
    return UnitOfWork(session)


def get_user_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserService:
    return UserService(uow)


def get_academic_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AcademicService:
    return AcademicService(uow)


def get_service_request_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ServiceRequestService:
    return ServiceRequestService(uow)


def get_file_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> FileService:
    return FileService(uow)


def get_quote_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> QuoteService:
    return QuoteService(uow)


def get_content_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ContentService:
    return ContentService(uow)


def get_campaign_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> CampaignService:
    return CampaignService(uow)


def get_telegram_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TelegramService:
    return TelegramService(uow)


def get_notification_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> NotificationService:
    return NotificationService(uow)


def get_audit_service(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AuditService:
    return AuditService(uow)
