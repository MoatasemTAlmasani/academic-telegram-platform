"""Secure Telegram webhook and first-touch bot interaction."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from backend.app.core.config import get_settings
from backend.app.infrastructure.telegram.client import TelegramClient

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
)


def _main_menu() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "📚 الخدمات الأكاديمية", "callback_data": "services"}],
            [
                {"text": "📝 تقديم طلب", "callback_data": "new_request"},
                {"text": "📂 طلباتي", "callback_data": "my_requests"},
            ],
            [
                {"text": "🔔 إشعاراتي", "callback_data": "notifications"},
                {"text": "👤 حسابي", "callback_data": "profile"},
            ],
            [{"text": "💬 الدعم والمساعدة", "callback_data": "support"}],
        ]
    }


def _welcome_text(first_name: str | None) -> str:
    name = first_name.strip() if first_name and first_name.strip() else ""
    greeting = f"مرحبًا {name} 👋" if name else "مرحبًا بك 👋"

    return (
        f"{greeting}\n\n"
        "🎓 <b>مرحبًا بك في منصة إحتراف للخدمات الأكاديمية</b>\n\n"
        "يسعدنا وجودك معنا 🌟\n\n"
        "من خلال المنصة يمكنك الوصول بسهولة إلى مجموعة من "
        "<b>الخدمات الأكاديمية</b>، وتقديم طلبك، متابعة حالته، "
        "والتواصل مع فريقنا — كل ذلك من مكان واحد.\n\n"
        "📚 <b>خدمات أكاديمية متنوعة</b>\n"
        "📝 <b>تقديم الطلبات بسهولة</b>\n"
        "📂 <b>رفع الملفات ومتابعة الطلب</b>\n"
        "🔔 <b>استقبال التحديثات والإشعارات</b>\n"
        "💬 <b>دعم ومساعدة عند الحاجة</b>\n\n"
        "اختر من القائمة أدناه للبدء 👇"
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

    if x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret.",
        )

    body = await request.json()
    message = body.get("message") or {}
    chat = message.get("chat") or {}

    if chat.get("type") != "private":
        return {"ok": True}

    chat_id = chat.get("id")

    if not isinstance(chat_id, int):
        return {"ok": True}

    text = str(message.get("text") or "").strip()

    if text == "/start" or text.startswith("/start "):
        if not settings.telegram_bot_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram bot token is not configured.",
            )

        telegram = TelegramClient(settings.telegram_bot_token)

        await telegram.send_message(
            chat_id=chat_id,
            text=_welcome_text(chat.get("first_name")),
            reply_markup=_main_menu(),
        )

    return {"ok": True}
