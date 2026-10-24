"""Administrative application settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_session
from backend.app.api.rbac_dependencies import require_permission
from backend.app.modules.authentication.permissions import Permission
from database.models import AppSettings


router = APIRouter(
    prefix="/admin/settings",
    tags=["admin-settings"],
)


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    app_name: str
    app_description: str | None
    environment: str
    default_language: str
    default_timezone: str
    support_email: str | None
    support_phone: str | None


class SettingsUpdateRequest(BaseModel):
    app_name: str
    app_description: str | None = None
    environment: str
    default_language: str
    default_timezone: str
    support_email: str | None = None
    support_phone: str | None = None


async def _get_or_create_settings(session: AsyncSession) -> AppSettings:
    result = await session.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    settings = result.scalar_one_or_none()

    if settings is None:
        settings = AppSettings(
            id=1,
            app_name="Academic Services Platform",
            app_description="Academic and student services platform",
            environment="development",
            default_language="en",
            default_timezone="Asia/Aden",
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)

    return settings


@router.get(
    "",
    response_model=SettingsResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def get_admin_settings(
    session: AsyncSession = Depends(get_session),
) -> AppSettings:
    return await _get_or_create_settings(session)


@router.patch(
    "",
    response_model=SettingsResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def update_admin_settings(
    payload: SettingsUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> AppSettings:
    settings = await _get_or_create_settings(session)

    settings.app_name = payload.app_name.strip()
    settings.app_description = (
        payload.app_description.strip()
        if payload.app_description
        else None
    )
    settings.environment = payload.environment.strip()
    settings.default_language = payload.default_language.strip()
    settings.default_timezone = payload.default_timezone.strip()
    settings.support_email = (
        payload.support_email.strip()
        if payload.support_email
        else None
    )
    settings.support_phone = (
        payload.support_phone.strip()
        if payload.support_phone
        else None
    )

    await session.commit()
    await session.refresh(settings)
    return settings
