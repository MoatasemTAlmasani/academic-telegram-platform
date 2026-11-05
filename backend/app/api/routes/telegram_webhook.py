"""Secure Telegram webhook backed by the full TelegramBotRunner handlers."""

from __future__ import annotations

import hmac
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from backend.app.core.config import get_settings
from backend.app.infrastructure.telegram.bot_runner import TelegramBotRunner

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    settings = get_settings()

    if settings.telegram_mode != "webhook":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram webhook delivery is disabled in polling mode.",
        )

    expected_secret = (
        settings.telegram_webhook_secret.get_secret_value().strip()
        if settings.telegram_webhook_secret
        else ""
    )
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram webhook secret is not configured.",
        )

    supplied_secret = x_telegram_bot_api_secret_token or ""
    if not hmac.compare_digest(supplied_secret, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret.",
        )

    if settings.telegram_bot_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot token is not configured.",
        )

    try:
        update: Any = await request.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram update payload.",
        ) from exc

    if not isinstance(update, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram update payload must be a JSON object.",
        )

    update_id = update.get("update_id")
    if type(update_id) is not int or update_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram update_id must be a non-negative integer.",
        )

    runner = TelegramBotRunner(settings.telegram_bot_token)
    try:
        await runner.process_webhook_update(update)
    except Exception:
        # Do not log the raw update: it may contain private user messages.
        logger.exception("Telegram webhook update processing failed (update_id=%s)", update_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram update could not be processed; Telegram may retry delivery.",
        ) from None

    return {"ok": True}
