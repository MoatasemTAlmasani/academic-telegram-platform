"""Shared Telegram message templates and menu keyboards."""

from __future__ import annotations

from typing import Any


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
