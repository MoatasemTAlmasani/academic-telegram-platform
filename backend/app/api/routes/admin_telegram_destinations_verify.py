"""Telegram destination verification API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.core.config import get_settings
from backend.app.infrastructure.persistence.database import get_session
from backend.app.infrastructure.telegram.client import TelegramAPIError, TelegramClient
from backend.app.modules.authentication.permissions import Permission
from database.models.enums import (
    TelegramBotStatus,
    TelegramChatType,
    TelegramPrivacyStatus,
    TelegramValidationStatus,
)
from database.models.telegram import TelegramDestination, TelegramValidationLog


router = APIRouter(
    prefix="/admin/telegram-destinations",
    tags=["admin-telegram-destinations"],
)


def _chat_type(value: str | None) -> TelegramChatType:
    if not value:
        return TelegramChatType.UNKNOWN

    normalized = value.strip().upper()

    try:
        return TelegramChatType(normalized)
    except ValueError:
        return TelegramChatType.UNKNOWN


def _normalize_identifier(destination: TelegramDestination) -> str:
    if destination.chat_id is not None:
        return str(destination.chat_id)

    if destination.username:
        return (
            destination.username
            if destination.username.startswith("@")
            else f"@{destination.username}"
        )

    value = destination.original_url.strip()

    if value.startswith("@"):
        return value

    parsed = urlparse(value)

    if parsed.netloc.lower() in {"t.me", "telegram.me"}:
        path = parsed.path.strip("/")

        if path and "/" not in path:
            return f"@{path}"

    if value.startswith("https://") or value.startswith("http://"):
        raise ValueError(
            "Telegram URL cannot be resolved automatically. "
            "Use a public t.me username link or an existing chat ID."
        )

    return value


@router.post(
    "/{destination_id}/verify",
    dependencies=[Depends(require_permission(Permission.SERVICES_UPDATE))],
)
async def verify_telegram_destination(
    destination_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    destination = await session.get(TelegramDestination, destination_id)

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail="Telegram destination not found.",
        )

    settings = get_settings()

    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=500,
            detail="Telegram bot token is not configured.",
        )

    checked_at = datetime.now(timezone.utc)
    client = TelegramClient(settings.telegram_bot_token)

    try:
        identifier = _normalize_identifier(destination)
        chat_response = await client.call(
            "getChat",
            {"chat_id": identifier},
        )
        chat = chat_response["result"]

        chat_id = chat.get("id")
        username = chat.get("username")
        title = chat.get("title") or chat.get("first_name")
        chat_type = _chat_type(chat.get("type"))

        destination.chat_id = chat_id
        destination.username = username
        destination.title = title
        destination.chat_type = chat_type

        if username:
            destination.normalized_identifier = f"@{username}"

        if username:
            destination.privacy_status = TelegramPrivacyStatus.PUBLIC
        else:
            destination.privacy_status = TelegramPrivacyStatus.PRIVATE

        me_response = await client.get_me()
        bot_user = me_response["result"]
        bot_id = bot_user["id"]

        try:
            member_response = await client.call(
                "getChatMember",
                {
                    "chat_id": chat_id,
                    "user_id": bot_id,
                },
            )
        except TelegramAPIError as exc:
            destination.bot_status = TelegramBotStatus.NOT_ADDED
            destination.can_post = None
            destination.validation_status = TelegramValidationStatus.BOT_NOT_ADDED
            destination.last_checked_at = checked_at
            destination.last_error = str(exc)

            log = TelegramValidationLog(
                destination_id=destination.id,
                status=TelegramValidationStatus.BOT_NOT_ADDED,
                bot_status=TelegramBotStatus.NOT_ADDED,
                can_post=None,
                error_message=str(exc),
                checked_at=checked_at,
            )

            session.add(log)
            await session.commit()
            await session.refresh(destination)

            return {
                "success": False,
                "status": TelegramValidationStatus.BOT_NOT_ADDED.value,
                "bot_status": TelegramBotStatus.NOT_ADDED.value,
                "can_post": None,
                "chat_id": destination.chat_id,
                "username": destination.username,
                "title": destination.title,
                "chat_type": destination.chat_type.value,
                "privacy_status": destination.privacy_status.value,
                "message": str(exc),
            }

        member = member_response["result"]
        member_status = member.get("status")

        if member_status in {"creator", "administrator", "member"}:
            destination.bot_status = TelegramBotStatus.ADDED
        else:
            destination.bot_status = TelegramBotStatus.NOT_ADDED

        can_post = True

        if member_status == "administrator":
            can_post = member.get("can_post_messages", True)

        elif chat_type in {
            TelegramChatType.GROUP,
            TelegramChatType.SUPERGROUP,
        }:
            can_post = member_status in {
                "creator",
                "administrator",
                "member",
            }

        destination.can_post = can_post

        if destination.bot_status != TelegramBotStatus.ADDED:
            status = TelegramValidationStatus.BOT_NOT_ADDED
            error_message = "Bot is not a member of this Telegram destination."

        elif not can_post:
            status = TelegramValidationStatus.NO_POST_PERMISSION
            error_message = "Bot does not have permission to post."

        else:
            status = TelegramValidationStatus.READY
            error_message = None

        destination.validation_status = status
        destination.last_checked_at = checked_at
        destination.last_error = error_message

        if status == TelegramValidationStatus.READY:
            destination.last_success_at = checked_at

        log = TelegramValidationLog(
            destination_id=destination.id,
            status=status,
            bot_status=destination.bot_status,
            can_post=can_post,
            error_message=error_message,
            checked_at=checked_at,
        )

        session.add(log)
        await session.commit()
        await session.refresh(destination)

        return {
            "success": True,
            "status": destination.validation_status.value,
            "bot_status": destination.bot_status.value,
            "can_post": destination.can_post,
            "chat_id": destination.chat_id,
            "username": destination.username,
            "title": destination.title,
            "chat_type": destination.chat_type.value,
            "privacy_status": destination.privacy_status.value,
            "message": error_message or "Telegram destination is ready for publishing.",
        }

    except TelegramAPIError as exc:
        destination.validation_status = TelegramValidationStatus.NOT_FOUND
        destination.bot_status = TelegramBotStatus.UNKNOWN
        destination.can_post = None
        destination.last_checked_at = checked_at
        destination.last_error = str(exc)

        log = TelegramValidationLog(
            destination_id=destination.id,
            status=TelegramValidationStatus.NOT_FOUND,
            bot_status=TelegramBotStatus.UNKNOWN,
            can_post=None,
            error_message=str(exc),
            checked_at=checked_at,
        )

        session.add(log)
        await session.commit()

        return {
            "success": False,
            "status": TelegramValidationStatus.NOT_FOUND.value,
            "bot_status": TelegramBotStatus.UNKNOWN.value,
            "can_post": None,
            "message": str(exc),
        }
