"""Telegram long-polling runner for development/free hosting."""

from __future__ import annotations

import asyncio
import calendar
import logging
from collections import deque
from typing import Any
from uuid import UUID

import httpx
from pydantic import SecretStr
from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.models.catalog import Category, Service
from database.models.enums import RequestPriority, ServiceRequestStatus, UserStatus
from database.models.identity import Role, User
from database.models.requests import ServiceRequest
from database.models.telegram_runtime import (
    TelegramConversationState,
    TelegramProcessedUpdate,
)

CATEGORY_PAGE_SIZE = 6
SERVICE_PAGE_SIZE = 8
from database.session import SessionLocal, engine

from backend.app.infrastructure.telegram.messages import (
    _main_menu,
    _welcome_text,
)

logger = logging.getLogger(__name__)


class TelegramBotRunner:
    """Run the Telegram Bot API through long polling."""

    def __init__(self, token: SecretStr) -> None:
        value = token.get_secret_value().strip()
        if not value:
            raise ValueError("Telegram bot token is empty.")

        self.base_url = f"https://api.telegram.org/bot{value}"
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._offset = 0
        self._conversation_state: dict[int, dict[str, Any]] = {}
        self._processed_update_ids: set[int] = set()
        self._processed_update_order: deque[int] = deque()
        self._active_update_id: int | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return

        await self._load_durable_state()
        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._run(),
            name="telegram-bot-polling",
        )
        logger.info("Telegram long polling started.")

    async def stop(self) -> None:
        self._stop_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            finally:
                self._task = None

        logger.info("Telegram long polling stopped.")

    async def wait(self) -> None:
        """Wait until the polling task ends, propagating an unexpected failure."""
        if self._task:
            await self._task

    async def _run(self) -> None:
        backoff = 2.0

        timeout = httpx.Timeout(
            connect=10.0,
            read=35.0,
            write=10.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                await self._api_call(
                    client,
                    "deleteWebhook",
                    {"drop_pending_updates": False},
                )
            except Exception:
                logger.exception(
                    "Unable to prepare Telegram polling mode."
                )
                raise

            while not self._stop_event.is_set():
                try:
                    result = await self._api_call(
                        client,
                        "getUpdates",
                        {
                            "offset": self._offset,
                            "timeout": 25,
                            "allowed_updates": [
                                "message",
                                "callback_query",
                                "my_chat_member",
                                "chat_member",
                                "chat_join_request",
                                "channel_post",
                                "edited_channel_post",
                            ],
                        },
                    )

                    backoff = 2.0

                    updates = result.get("result", [])
                    if updates:
                        logger.warning(
                            "POLLING UPDATE RECEIVED: count=%s updates=%s",
                            len(updates),
                            [u.get("update_id") for u in updates],
                        )

                    for update in updates:
                        update_id = update.get("update_id")

                        if (
                            isinstance(update_id, int)
                            and await self._is_update_processed(update_id)
                        ):
                            self._offset = max(self._offset, update_id + 1)
                            continue

                        try:
                            self._active_update_id = (
                                update_id if isinstance(update_id, int) else None
                            )
                            await self._handle_update(
                                client,
                                update,
                            )
                            chat_id = self._chat_id_for_update(update)
                            if chat_id is not None:
                                await self._persist_conversation_state(chat_id)
                            if isinstance(update_id, int):
                                await self._mark_update_processed(
                                    update_id,
                                    self._update_type(update),
                                )
                                self._offset = max(
                                    self._offset,
                                    update_id + 1,
                                )
                        except Exception:
                            logger.exception(
                                "Failed to process Telegram update %s",
                                update_id,
                            )
                            # Keep the offset unchanged so Telegram redelivers
                            # this update after a transient processing failure.
                            break
                        finally:
                            self._active_update_id = None

                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception(
                        "Telegram polling failed; retrying."
                    )

                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=backoff,
                        )
                    except asyncio.TimeoutError:
                        backoff = min(backoff * 2, 30.0)

    async def _api_call(
        self,
        client: httpx.AsyncClient,
        method: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await client.post(
            f"{self.base_url}/{method}",
            json=payload or {},
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                data.get("description")
                or f"Telegram API error: {method}"
            )

        return data

    async def _handle_update(
        self,
        client: httpx.AsyncClient,
        update: dict[str, Any],
    ) -> None:
        update_id = update.get("update_id")
        if (
            isinstance(update_id, int)
            and update_id in self._processed_update_ids
        ):
            logger.debug("Ignoring duplicate Telegram update %s", update_id)
            return

        message = update.get("message")

        if isinstance(message, dict):
            await self._handle_message(client, message)
            return

        callback_query = update.get("callback_query")

        if isinstance(callback_query, dict):
            await self._handle_callback_query(client, callback_query)

    @staticmethod
    def _update_type(update: dict[str, Any]) -> str:
        return next(
            (
                key
                for key in update
                if key != "update_id" and isinstance(update.get(key), dict)
            ),
            "unknown",
        )[:80]

    @staticmethod
    def _chat_id_for_update(update: dict[str, Any]) -> int | None:
        message = update.get("message")
        if isinstance(message, dict):
            chat_id = (message.get("chat") or {}).get("id")
            return chat_id if isinstance(chat_id, int) else None

        callback_query = update.get("callback_query")
        if isinstance(callback_query, dict):
            message = callback_query.get("message") or {}
            chat_id = (message.get("chat") or {}).get("id")
            return chat_id if isinstance(chat_id, int) else None
        return None

    async def _load_durable_state(self) -> None:
        async with SessionLocal() as session:
            states = await session.execute(
                select(TelegramConversationState)
            )
            self._conversation_state = {
                int(row.chat_id): dict(row.state)
                for row in states.scalars()
            }
            processed = await session.execute(
                select(TelegramProcessedUpdate.update_id)
                .order_by(TelegramProcessedUpdate.update_id.desc())
                .limit(1024)
            )
            update_ids = list(reversed(processed.scalars().all()))
            self._processed_update_order = deque(update_ids)
            self._processed_update_ids = set(update_ids)
            latest = await session.execute(
                select(func.max(TelegramProcessedUpdate.update_id))
            )
            last_update_id = latest.scalar_one_or_none()
            self._offset = int(last_update_id or -1) + 1

    async def _is_update_processed(self, update_id: int) -> bool:
        if update_id in self._processed_update_ids:
            return True
        async with SessionLocal() as session:
            return (
                await session.get(TelegramProcessedUpdate, update_id)
            ) is not None

    async def _mark_update_processed(self, update_id: int, update_type: str) -> None:
        async with SessionLocal() as session:
            statement = (
                pg_insert(TelegramProcessedUpdate)
                .values(update_id=update_id, update_type=update_type)
                .on_conflict_do_nothing(
                    index_elements=[TelegramProcessedUpdate.update_id]
                )
            )
            await session.execute(statement)
            if update_id % 100 == 0:
                await session.execute(
                    delete(TelegramProcessedUpdate).where(
                        TelegramProcessedUpdate.update_id < update_id - 10_000
                    )
                )
            await session.commit()
        self._remember_processed_update(update_id)

    async def _persist_conversation_state(self, chat_id: int) -> None:
        state = self._conversation_state.get(chat_id)
        async with SessionLocal() as session:
            record = await session.get(TelegramConversationState, chat_id)
            if state is None:
                if record is not None:
                    await session.delete(record)
            elif record is None:
                session.add(
                    TelegramConversationState(
                        chat_id=chat_id,
                        state=dict(state),
                    )
                )
            else:
                record.state = dict(state)
            await session.commit()

    def _remember_processed_update(self, update_id: int) -> None:
        """Remember recent update IDs so a repeated Telegram delivery is inert."""
        self._processed_update_ids.add(update_id)
        self._processed_update_order.append(update_id)
        while len(self._processed_update_order) > 1024:
            expired_update_id = self._processed_update_order.popleft()
            self._processed_update_ids.discard(expired_update_id)

    async def process_webhook_update(self, update: dict[str, Any]) -> bool:
        """Process one webhook update using the same handlers as long polling.

        A PostgreSQL advisory lock serializes duplicate deliveries of the same
        Telegram update across concurrent serverless invocations.
        """
        update_id = update.get("update_id")
        if type(update_id) is not int or update_id < 0:
            raise ValueError("Telegram update_id must be a non-negative integer.")

        # Lock both the update and its private chat. The chat lock prevents
        # concurrent messages from overwriting each other's conversation state.
        lock_keys = [f"telegram-update:{update_id}"]
        chat_id = self._chat_id_for_update(update)
        if chat_id is not None:
            lock_keys.append(f"telegram-chat:{chat_id}")
        lock_keys = sorted(set(lock_keys))

        async with engine.connect() as lock_connection:
            acquired: list[str] = []
            try:
                for lock_key in lock_keys:
                    await lock_connection.execute(
                        text("SELECT pg_advisory_lock(hashtextextended(:lock_key, 0))"),
                        {"lock_key": lock_key},
                    )
                    acquired.append(lock_key)
                await lock_connection.commit()

                await self._load_durable_state()
                if await self._is_update_processed(update_id):
                    return False

                self._active_update_id = update_id
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=10.0,
                        read=20.0,
                        write=10.0,
                        pool=10.0,
                    )
                ) as client:
                    await self._handle_update(client, update)

                if chat_id is not None:
                    await self._persist_conversation_state(chat_id)

                await self._mark_update_processed(
                    update_id,
                    self._update_type(update),
                )
                return True
            finally:
                self._active_update_id = None
                for lock_key in reversed(acquired):
                    await lock_connection.execute(
                        text("SELECT pg_advisory_unlock(hashtextextended(:lock_key, 0))"),
                        {"lock_key": lock_key},
                    )
                await lock_connection.commit()

    async def _send_deadline_calendar(
        self,
        client: httpx.AsyncClient,
        chat_id: int,
        year: int | None = None,
        month: int | None = None,
    ) -> None:
        from datetime import date

        today = date.today()

        year = year or today.year
        month = month or today.month

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        month_name = [
            "",
            "يناير",
            "فبراير",
            "مارس",
            "أبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
        ][month]

        keyboard = [
            [
                {"text": "السبت", "callback_data": "calendar_noop"},
                {"text": "الأحد", "callback_data": "calendar_noop"},
                {"text": "الاثنين", "callback_data": "calendar_noop"},
                {"text": "الثلاثاء", "callback_data": "calendar_noop"},
                {"text": "الأربعاء", "callback_data": "calendar_noop"},
                {"text": "الخميس", "callback_data": "calendar_noop"},
                {"text": "الجمعة", "callback_data": "calendar_noop"},
            ]
        ]

        weeks = calendar.monthcalendar(year, month)

        for week in weeks:
            row = []
            for day in week:
                if day == 0:
                    row.append({"text": " ", "callback_data": "calendar_noop"})
                    continue

                selected_date = date(year, month, day)

                if selected_date < today:
                    row.append({"text": "·", "callback_data": "calendar_noop"})
                else:
                    row.append({
                        "text": str(day),
                        "callback_data": f"deadline:{selected_date.isoformat()}",
                    })

            keyboard.append(row)

        keyboard.append([
            {
                "text": "◀️ السابق",
                "callback_data": f"calendar:{year}:{month - 1}",
            },
            {
                "text": f"{month_name} {year}",
                "callback_data": "calendar_noop",
            },
            {
                "text": "التالي ▶️",
                "callback_data": f"calendar:{year}:{month + 1}",
            },
        ])

        keyboard.append([
            {"text": "⏭️ بدون موعد", "callback_data": "deadline:none"}
        ])
        keyboard.append([
            {"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}
        ])

        await self._api_call(
            client,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": (
                    "📅 <b>اختيار الموعد النهائي</b>\n\n"
                    "اختر التاريخ المطلوب من التقويم:"
                ),
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard},
            },
        )

    async def _handle_callback_query(
        self,
        client: httpx.AsyncClient,
        callback_query: dict[str, Any],
    ) -> None:
        callback_id = callback_query.get("id")
        data = str(callback_query.get("data") or "").strip()
        message = callback_query.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")

        if isinstance(callback_id, str):
            await self._api_call(
                client,
                "answerCallbackQuery",
                {"callback_query_id": callback_id},
            )

        if not isinstance(chat_id, int):
            return

        if data == "services":
            await self._send_categories(client, chat_id, 0)
            return

        if data.startswith("categories_page:"):
            page = int(data.split(":", 1)[1])
            await self._send_categories(client, chat_id, page)
            return

        if data.startswith("services_page:"):
            parts = data.split(":")
            category_id = parts[1]
            page = int(parts[2])
            await self._send_services(client, chat_id, category_id, page)
            return

        if data.startswith("category:"):
            await self._send_services(client, chat_id, data.split(":", 1)[1])
            return

        if data.startswith("service:"):
            await self._send_service_details(client, chat_id, data.split(":", 1)[1])
            return

        if data.startswith("request:"):
            service_id = data.split(":", 1)[1]
            active_state = self._conversation_state.get(chat_id)
            if active_state is not None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": (
                            "لديك طلب قيد الإنشاء بالفعل. أكمل الطلب الحالي "
                            "أو ألغِه قبل بدء طلب آخر."
                        ),
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "❌ إلغاء الطلب الحالي",
                                        "callback_data": "request_cancel",
                                    }
                                ]
                            ]
                        },
                    },
                )
                return

            state = {
                "stage": "description",
                "service_id": service_id,
                "chat_id": chat_id,
            }
            self._conversation_state[chat_id] = state

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "📝 <b>تقديم طلب جديد</b>\\n\\n"
                        "<b>الخطوة 1 — تفاصيل الطلب</b>\\n\\n"
                        "اختر طريقة إضافة تفاصيل طلبك:"
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "✍️ كتابة الوصف", "callback_data": "request_add_description"}],
                            [{"text": "📎 رفع ملف", "callback_data": "request_add_file"}],
                            [{"text": "⏭️ استخدام وصف الخدمة", "callback_data": "request_use_default_description"}],
                            [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                        ]
                    }
                }
            )
            return

        if data == "request_add_title":
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "title":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            state["stage"] = "title_input"

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": "✏️ <b>إضافة عنوان الطلب</b>\\n\\nاكتب عنوان طلبك الآن.",
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "force_reply": True,
                        "input_field_placeholder": "اكتب عنوان الطلب هنا..."
                    }
                }
            )
            return

        if data == "request_add_description":
            state = self._conversation_state.get(chat_id)
            if not state:
                logger.warning(
                    "REQUEST DESCRIPTION: missing state for chat_id=%s; states=%s",
                    chat_id, list(self._conversation_state.keys())
                )
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. اضغط على الخدمة وابدأ طلبًا جديدًا."}
                )
                return

            if state.get("stage") == "description_input":
                # A repeated tap must not replace the active reply prompt.
                return

            if state.get("stage") != "description":
                logger.warning(
                    "REQUEST DESCRIPTION: unexpected stage=%r for chat_id=%s",
                    state.get("stage"), chat_id
                )
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ تغيّرت خطوة الطلب. اضغط على الخدمة وابدأ طلبًا جديدًا."}
                )
                return

            state["stage"] = "description_input"

            response = await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "📝 <b>وصف الطلب</b>\\n\\n"
                        "اكتب تفاصيل طلبك الآن.\\n"
                        "يمكنك توضيح المطلوب، المتطلبات، والهدف من الخدمة."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "force_reply": True,
                        "input_field_placeholder": "اكتب تفاصيل طلبك هنا..."
                    }
                }
            )
            prompt = response.get("result") or {}
            state["expected_prompt_message_id"] = prompt.get("message_id")
            return

        if data.startswith("specialization:"):
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "specialization":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            specialization = data.split(":", 1)[1]
            state["specialization"] = None if specialization == "none" else specialization
            state["stage"] = "deadline"

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🎓 تم حفظ التخصص: "
                        + ("بدون تخصص" if specialization == "none" else specialization)
                        + "\\n\\n"
                        "📅 <b>الخطوة التالية — الموعد النهائي</b>\\n\\n"
                        "اختر التاريخ المطلوب من التقويم."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "📅 اختيار الموعد", "callback_data": "request_add_deadline"}],
                            [{"text": "⏭️ بدون موعد", "callback_data": "deadline:none"}],
                            [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                        ]
                    }
                }
            )
            return

        if data == "specialization_search":
            state = self._conversation_state.get(chat_id)
            if not state:
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            if state.get("stage") == "specialization_search_input":
                # Avoid replacing the prompt when Telegram repeats a callback.
                return

            if state.get("stage") != "specialization":
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تغيّرت خطوة الطلب. استخدم أزرار الخطوة الحالية.",
                    },
                )
                return

            state["stage"] = "specialization_search_input"

            response = await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🔎 <b>البحث عن تخصص</b>\\n\\n"
                        "اكتب اسم التخصص الذي تبحث عنه."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "force_reply": True,
                        "input_field_placeholder": "مثال: هندسة البرمجيات"
                    }
                }
            )
            prompt = response.get("result") or {}
            state["expected_prompt_message_id"] = prompt.get("message_id")
            return

        if data == "request_add_specialization":
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "specialization":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            state["stage"] = "specialization"

            specializations = [
                ("💻 تقنية المعلومات", "تقنية المعلومات"),
                ("🖥️ علوم الحاسوب", "علوم الحاسوب"),
                ("🌐 هندسة الشبكات", "هندسة الشبكات"),
                ("🔐 الأمن السيبراني", "الأمن السيبراني"),
                ("🤖 الذكاء الاصطناعي", "الذكاء الاصطناعي"),
                ("📊 علم البيانات", "علم البيانات"),
                ("💾 نظم المعلومات", "نظم المعلومات"),
                ("⚙️ الهندسة", "الهندسة"),
                ("🏗️ الهندسة المدنية", "الهندسة المدنية"),
                ("⚡ الهندسة الكهربائية", "الهندسة الكهربائية"),
                ("📡 هندسة الاتصالات", "هندسة الاتصالات"),
                ("💼 إدارة الأعمال", "إدارة الأعمال"),
                ("📈 المحاسبة", "المحاسبة"),
                ("⚖️ القانون", "القانون"),
                ("🩺 الطب", "الطب"),
                ("💊 الصيدلة", "الصيدلة"),
                ("🦷 طب الأسنان", "طب الأسنان"),
                ("🔬 العلوم", "العلوم"),
                ("📚 اللغة العربية", "اللغة العربية"),
                ("🌍 اللغة الإنجليزية", "اللغة الإنجليزية"),
            ]

            keyboard = []
            for i in range(0, len(specializations), 2):
                row = []
                for label, value in specializations[i:i + 2]:
                    row.append({
                        "text": label,
                        "callback_data": f"specialization:{value}"
                    })
                keyboard.append(row)

            keyboard.append([
                {"text": "🔎 البحث عن تخصص", "callback_data": "specialization_search"}
            ])
            keyboard.append([
                {"text": "⏭️ بدون تخصص", "callback_data": "specialization:none"}
            ])

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🎓 <b>اختر تخصصك</b>\\n\\n"
                        "اختر تخصصك من القائمة، أو استخدم البحث إذا لم تجده."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": keyboard}
                }
            )
            return

        if data == "request_add_deadline":
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "deadline":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            state["stage"] = "deadline"

            await self._send_deadline_calendar(client, chat_id)
            return

        if data.startswith("calendar:"):
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "deadline":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            parts = data.split(":")
            if len(parts) != 3:
                return

            year = int(parts[1])
            month = int(parts[2])

            await self._send_deadline_calendar(
                client,
                chat_id,
                year,
                month,
            )
            return

        if data.startswith("deadline:"):
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "deadline":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            deadline = data.split(":", 1)[1]

            state["deadline"] = deadline
            state["stage"] = "confirm"

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "📅 <b>تم اختيار الموعد النهائي</b>\\n\\n"
                        f"الموعد: <b>{deadline}</b>\\n\\n"
                        "سيتم الانتقال إلى مراجعة الطلب."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "👀 مراجعة الطلب", "callback_data": "request_review"}],
                            [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                        ]
                    }
                }
            )
            return

        if data == "deadline:none":
            state = self._conversation_state.get(chat_id)
            if not state or state.get("stage") != "deadline":
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."}
                )
                return

            state["deadline"] = None
            state["stage"] = "confirm"

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "📅 <b>الموعد النهائي</b>\\n\\n"
                        "تم اختيار: بدون موعد.\\n\\n"
                        "سيتم الانتقال إلى مراجعة الطلب."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "👀 مراجعة الطلب", "callback_data": "request_review"}],
                            [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                        ]
                    }
                }
            )
            return

        if data == "calendar_noop":
            return

        if data == "request_cancel":
            self._conversation_state.pop(chat_id, None)
            await self._api_call(client, "sendMessage", {"chat_id": chat_id, "text": "❌ تم إلغاء الطلب."})
            return

        if data == "request_review":
            state = self._conversation_state.get(chat_id)

            if not state or not state.get("service_id"):
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."
                    }
                )
                return

            from uuid import UUID

            async with SessionLocal() as session:
                result = await session.execute(
                    select(Service).where(
                        Service.id == UUID(str(state["service_id"])),
                        Service.deleted_at.is_(None),
                    )
                )
                service = result.scalar_one_or_none()

            if service is None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تعذر العثور على الخدمة."
                    }
                )
                return

            description = state.get("description") or "لم تتم إضافة وصف."
            specialization = state.get("specialization") or "بدون تخصص"
            deadline = state.get("deadline") or "بدون موعد"

            review_text = (
                "👀 <b>مراجعة الطلب قبل الإرسال</b>\\n\\n"
                f"📚 <b>الخدمة:</b> {service.name}\\n"
                f"📝 <b>الوصف:</b> {description}\\n"
                f"🎓 <b>التخصص:</b> {specialization}\\n"
                f"📅 <b>الموعد النهائي:</b> {deadline}\\n\\n"
                "هل تريد إرسال الطلب؟"
            )

            state["stage"] = "confirm"

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": review_text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "✅ تأكيد وإرسال", "callback_data": "request_confirm"}],
                            [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                        ]
                    }
                }
            )
            return

        if data == "request_confirm":
            state = self._conversation_state.get(chat_id)

            if not state or not state.get("service_id"):
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ انتهت جلسة الطلب. يرجى بدء طلب جديد."
                    }
                )
                return

            user = await self._get_or_create_user(
                {"from": callback_query.get("from") or {}}
            )

            if user is None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تعذر تحديد حسابك."
                    }
                )
                return

            from uuid import UUID

            try:
                async with SessionLocal() as session:
                    result = await session.execute(
                        select(Service).where(
                            Service.id == UUID(str(state["service_id"])),
                            Service.deleted_at.is_(None),
                        )
                    )
                    service = result.scalar_one_or_none()

                    if service is None:
                        await self._api_call(
                            client,
                            "sendMessage",
                            {
                                "chat_id": chat_id,
                                "text": "⚠️ تعذر العثور على الخدمة."
                            }
                        )
                        return

                    existing_request = None
                    if self._active_update_id is not None:
                        existing_result = await session.execute(
                            select(ServiceRequest).where(
                                ServiceRequest.telegram_update_id
                                == self._active_update_id
                            )
                        )
                        existing_request = existing_result.scalar_one_or_none()

                    if existing_request is None:
                        request = ServiceRequest(
                            customer_id=user.id,
                            service_id=service.id,
                            title=service.name,
                            description=state.get("description"),
                            specialization=state.get("specialization"),
                            deadline=state.get("deadline"),
                            status=ServiceRequestStatus.NEW,
                            priority=RequestPriority.NORMAL,
                            telegram_update_id=self._active_update_id,
                        )

                        session.add(request)
                        await session.commit()

            except Exception:
                logger.exception(
                    "REQUEST_CONFIRM_SAVE_FAILED: chat_id=%s",
                    chat_id,
                )
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": (
                            "⚠️ تعذر حفظ طلبك بسبب خطأ أثناء الإرسال. "
                            "احتفظنا ببيانات الطلب؛ يرجى المحاولة لاحقًا."
                        )
                    }
                )
                return

            self._conversation_state.pop(chat_id, None)

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🎉 <b>تم إرسال طلبك بنجاح</b>\\n\\n"
                        "سيتم مراجعة الطلب من فريقنا والتواصل معك عند تحديث حالته."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "📂 طلباتي", "callback_data": "my_requests"}],
                            [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
                        ]
                    }
                }
            )
            return

        if data == "main_menu":
            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": _welcome_text(chat.get("first_name")),
                    "parse_mode": "HTML",
                    "reply_markup": _main_menu(),
                },
            )
            return

        if data == "my_requests":
    
            user = await self._get_or_create_user({"from": callback_query.get("from") or {}})

            if user is None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تعذر تحديد حسابك.",
                    },
                )
                return

            async with SessionLocal() as session:
                result = await session.execute(
                    select(ServiceRequest)
                    .where(
                        ServiceRequest.customer_id == user.id,
                        ServiceRequest.deleted_at.is_(None),
                    )
                    .order_by(ServiceRequest.created_at.desc())
                )
                requests = result.scalars().all()

            if not requests:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "📂 <b>طلباتي</b>\n\nليس لديك أي طلبات حتى الآن.",
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "📝 تقديم طلب", "callback_data": "new_request"}],
                                [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
                            ]
                        },
                    },
                )
                return

            status_names = {
                "NEW": "🆕 جديد",
                "UNDER_REVIEW": "🔎 قيد المراجعة",
                "WAITING_FOR_CUSTOMER": "⏳ بانتظارك",
                "QUOTATION_SENT": "💰 عرض سعر مرسل",
                "APPROVED": "✅ تمت الموافقة",
                "IN_PROGRESS": "⚙️ قيد التنفيذ",
                "COMPLETED": "🎉 مكتمل",
                "CANCELLED": "❌ ملغي",
                "REJECTED": "🚫 مرفوض",
            }

            lines = ["📂 <b>طلباتي</b>", ""]

            for index, item in enumerate(requests, 1):
                status_value = (
                    item.status.value
                    if hasattr(item.status, "value")
                    else str(item.status)
                )
                status_text = status_names.get(status_value, status_value)

                created = (
                    item.created_at.strftime("%Y-%m-%d")
                    if item.created_at
                    else "-"
                )

                lines.extend([
                    f"<b>{index}. {item.title}</b>",
                    f"📊 الحالة: {status_text}",
                    f"📅 تاريخ الطلب: {created}",
                    "",
                ])

            lines.append("اختر من القائمة الرئيسية لمتابعة خدماتك.")

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": "\n".join(lines),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🔄 تحديث الطلبات", "callback_data": "my_requests"}],
                            [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
                        ]
                    },
                },
            )
            return

        if data == "profile":

            user = await self._get_or_create_user({"from": callback_query.get("from") or {}})

            if user is None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تعذر تحديد حسابك.",
                    },
                )
                return

            async with SessionLocal() as session:
                result = await session.execute(
                    select(ServiceRequest).where(
                        ServiceRequest.customer_id == user.id,
                        ServiceRequest.deleted_at.is_(None),
                    )
                )
                user_requests = result.scalars().all()

            telegram_user = callback_query.get("from") or {}

            first_name = telegram_user.get("first_name") or "-"
            last_name = telegram_user.get("last_name") or ""
            username = telegram_user.get("username")
            full_name = f"{first_name} {last_name}".strip()

            username_text = f"@{username}" if username else "غير محدد"

            text = (
                "👤 <b>حسابي</b>\n\n"
                f"👨‍💼 <b>الاسم:</b> {full_name}\n"
                f"📱 <b>اسم المستخدم:</b> {username_text}\n"
                f"🆔 <b>Telegram ID:</b> {chat_id}\n"
                f"📋 <b>عدد الطلبات:</b> {len(user_requests)}\n"
            )

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "📂 طلباتي", "callback_data": "my_requests"}],
                            [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
                        ]
                    },
                },
            )
            return

        if data == "notifications":
            from database.models.notifications import Notification

            user = await self._get_or_create_user({"from": callback_query.get("from") or {}})

            if user is None:
                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚠️ تعذر تحديد حسابك.",
                    },
                )
                return

            async with SessionLocal() as session:
                result = await session.execute(
                    select(Notification)
                    .where(
                        Notification.user_id == user.id,
                        Notification.deleted_at.is_(None),
                    )
                    .order_by(Notification.created_at.desc())
                    .limit(20)
                )
                notifications = result.scalars().all()

            if not notifications:
                text = (
                    "🔔 <b>إشعاراتي</b>\n\n"
                    "لا توجد إشعارات جديدة حاليًا."
                )
            else:
                lines = ["🔔 <b>إشعاراتي</b>", ""]

                for item in notifications:
                    title = getattr(item, "title", None) or "إشعار"
                    message = getattr(item, "message", None) or ""
                    lines.append(f"🔹 <b>{title}</b>")
                    if message:
                        lines.append(message)
                    lines.append("")

                text = "\n".join(lines)

            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🔄 تحديث الإشعارات", "callback_data": "notifications"}],
                            [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
                        ]
                    },
                },
            )
            return

        responses = {
            "new_request": "📝 تقديم طلب\n\nاختر الخدمة أولًا من الخدمات الأكاديمية، ثم يمكنك تقديم طلبك.",
            "support": "💬 الدعم والمساعدة\n\nللتواصل مع فريق الدعم، سيتم تجهيز هذه الخدمة هنا.",
        }

        response = responses.get(data)
        if response:
            await self._api_call(
                client,
                "sendMessage",
                {"chat_id": chat_id, "text": response},
            )

    async def _send_categories(
        self,
        client,
        chat_id: int,
        page: int = 0,
    ):
        async with SessionLocal() as session:
            result = await session.execute(
                select(Category)
                .where(
                    Category.is_active.is_(True),
                    Category.deleted_at.is_(None),
                )
                .order_by(Category.sort_order, Category.name)
            )
            categories = result.scalars().all()

        total = len(categories)
        total_pages = max(1, (total + CATEGORY_PAGE_SIZE - 1) // CATEGORY_PAGE_SIZE)

        page = max(0, min(page, total_pages - 1))

        start_index = page * CATEGORY_PAGE_SIZE
        page_categories = categories[
            start_index:start_index + CATEGORY_PAGE_SIZE
        ]

        keyboard = [
            [
                {
                    "text": f"📚 {category.name}",
                    "callback_data": f"category:{category.id}",
                }
            ]
            for category in page_categories
        ]

        navigation = []

        if page > 0:
            navigation.append(
                {
                    "text": "⬅️ السابق",
                    "callback_data": f"categories_page:{page - 1}",
                }
            )

        navigation.append(
            {
                "text": f"📄 {page + 1}/{total_pages}",
                "callback_data": "noop",
            }
        )

        if page < total_pages - 1:
            navigation.append(
                {
                    "text": "التالي ➡️",
                    "callback_data": f"categories_page:{page + 1}",
                }
            )

        if navigation:
            keyboard.append(navigation)

        keyboard.append(
            [
                {
                    "text": "🏠 القائمة الرئيسية",
                    "callback_data": "main_menu",
                }
            ]
        )

        text = (
            "📚 <b>الخدمات الأكاديمية</b>\n\n"
            "اختر المجال الذي تحتاج إليه:\n\n"
            f"📊 <b>{total}</b> تخصصًا متاحًا\n"
            f"📄 الصفحة <b>{page + 1}</b> من <b>{total_pages}</b>"
        )

        await self._api_call(
            client,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard},
            },
        )

    async def _send_services(
        self,
        client,
        chat_id: int,
        category_id: str,
        page: int = 0,
    ):
        try:
            category_uuid = UUID(category_id)
        except ValueError:
            return

        async with SessionLocal() as session:
            category_result = await session.execute(
                select(Category).where(
                    Category.id == category_uuid,
                    Category.is_active.is_(True),
                    Category.deleted_at.is_(None),
                )
            )
            category = category_result.scalar_one_or_none()

            if category is None:
                return

            result = await session.execute(
                select(Service)
                .where(
                    Service.category_id == category_uuid,
                    Service.is_active.is_(True),
                    Service.deleted_at.is_(None),
                )
                .order_by(Service.sort_order, Service.name)
            )
            services = result.scalars().all()

        total = len(services)
        total_pages = max(1, (total + SERVICE_PAGE_SIZE - 1) // SERVICE_PAGE_SIZE)

        page = max(0, min(page, total_pages - 1))

        start_index = page * SERVICE_PAGE_SIZE
        page_services = services[
            start_index:start_index + SERVICE_PAGE_SIZE
        ]

        keyboard = [
            [
                {
                    "text": f"📌 {service.name}",
                    "callback_data": f"service:{service.id}",
                }
            ]
            for service in page_services
        ]

        navigation = []

        if page > 0:
            navigation.append(
                {
                    "text": "⬅️ السابق",
                    "callback_data": f"services_page:{category.id}:{page - 1}",
                }
            )

        navigation.append(
            {
                "text": f"📄 {page + 1}/{total_pages}",
                "callback_data": "noop",
            }
        )

        if page < total_pages - 1:
            navigation.append(
                {
                    "text": "التالي ➡️",
                    "callback_data": f"services_page:{category.id}:{page + 1}",
                }
            )

        if navigation:
            keyboard.append(navigation)

        keyboard.append(
            [
                {
                    "text": "⬅️ التصنيفات",
                    "callback_data": "services",
                },
                {
                    "text": "🏠 الرئيسية",
                    "callback_data": "main_menu",
                },
            ]
        )

        text = (
            f"📂 <b>{category.name}</b>\n\n"
            "اختر الخدمة التي تحتاج إليها:\n\n"
            f"📊 <b>{total}</b> خدمة متاحة\n"
            f"📄 الصفحة <b>{page + 1}</b> من <b>{total_pages}</b>"
        )

        await self._api_call(
            client,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard},
            },
        )

    async def _send_service_details(
        self,
        client: httpx.AsyncClient,
        chat_id: int,
        service_id: str,
    ) -> None:
        try:
            service_uuid = UUID(service_id)
        except ValueError:
            return

        async with SessionLocal() as session:
            result = await session.execute(
                select(Service, Category)
                .join(Category, Service.category_id == Category.id)
                .where(
                    Service.id == service_uuid,
                    Service.is_active.is_(True),
                    Service.deleted_at.is_(None),
                    Category.is_active.is_(True),
                    Category.deleted_at.is_(None),
                )
            )
            row = result.first()

        if row is None:
            return

        service, category = row
        description = service.description or service.short_description or "لا يوجد وصف متاح لهذه الخدمة حاليًا."
        text = (
            f"📌 <b>{service.name}</b>\n\n"
            f"📂 القسم: <b>{category.name}</b>\n\n"
            f"{description}"
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "📝 تقديم طلب لهذه الخدمة", "callback_data": f"request:{service.id}"}],
                [{"text": "⬅️ الخدمات", "callback_data": "services"}],
                [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}],
            ]
        }

        await self._api_call(
            client,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
        )

    async def _get_or_create_user(
        self,
        message: dict[str, Any],
    ) -> User | None:
        from_user = message.get("from") or {}
        telegram_user_id = from_user.get("id")

        if not isinstance(telegram_user_id, int):
            return None

        username = from_user.get("username")
        first_name = from_user.get("first_name")
        last_name = from_user.get("last_name")

        async with SessionLocal() as session:
            result = await session.execute(
                select(User).where(
                    User.telegram_user_id == telegram_user_id,
                    User.deleted_at.is_(None),
                )
            )
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    telegram_user_id=telegram_user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language="ar",
                    status=UserStatus.ACTIVE,
                )
                session.add(user)
            else:
                if str(user.status).upper() != UserStatus.ACTIVE.value:
                    return None
                user.username = username
                user.first_name = first_name
                user.last_name = last_name

            role_result = await session.execute(
                select(Role).where(Role.name == "customer")
            )
            customer_role = role_result.scalar_one_or_none()
            if customer_role is None:
                customer_role = Role(
                    name="customer",
                    description="Customer account",
                )
                session.add(customer_role)
            if not any(role.name == "customer" for role in user.roles):
                user.roles.append(customer_role)

            await session.commit()
            await session.refresh(user)
            return user

    async def _handle_message(
        self,
        client: httpx.AsyncClient,
        message: dict[str, Any],
    ) -> None:
        chat = message.get("chat") or {}

        if chat.get("type") != "private":
            return

        chat_id = chat.get("id")

        if not isinstance(chat_id, int):
            return

        text = str(message.get("text") or "").strip()
        logger.debug("Telegram private message received (text_present=%s)", bool(text))
        state = self._conversation_state.get(chat_id)

        if state is not None and text != "/start":
            if text == "/cancel":
                self._conversation_state.pop(chat_id, None)
                await self._api_call(
                    client,
                    "sendMessage",
                    {"chat_id": chat_id, "text": "❌ تم إلغاء الطلب."}
                )
                return

            stage = state.get("stage")

            if stage in (
                "description_input",
                "specialization_search_input",
            ):
                expected_prompt_id = state.get("expected_prompt_message_id")
                reply = message.get("reply_to_message") or {}
                reply_message_id = reply.get("message_id")
                if (
                    not isinstance(expected_prompt_id, int)
                    or reply_message_id != expected_prompt_id
                ):
                    await self._api_call(
                        client,
                        "sendMessage",
                        {
                            "chat_id": chat_id,
                            "text": "يرجى الرد مباشرة على رسالة السؤال لإكمال هذه الخطوة.",
                        },
                    )
                    return

                message_id = message.get("message_id")
                last_message_id = state.get("last_processed_message_id")
                if (
                    isinstance(message_id, int)
                    and isinstance(last_message_id, int)
                    and message_id <= last_message_id
                ):
                    logger.debug(
                        "Ignoring duplicate request input message %s",
                        message_id,
                    )
                    return

            if stage == "description_input" and text:
                state["description"] = text
                state["stage"] = "specialization"
                state.pop("expected_prompt_message_id", None)
                if isinstance(message.get("message_id"), int):
                    state["last_processed_message_id"] = message["message_id"]

                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": (
                            "🎓 <b>الخطوة 2 — التخصص</b>\\n\\n"
                            "اختر تخصصك من القائمة أو ابحث عنه."
                        ),
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "🎓 اختيار التخصص", "callback_data": "request_add_specialization"}
                                ],
                                [
                                    {"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}
                                ],
                            ]
                        }
                    }
                )
                return

            if stage == "specialization_search_input" and text:
                if isinstance(message.get("message_id"), int):
                    state["last_processed_message_id"] = message["message_id"]
                state.pop("expected_prompt_message_id", None)
                specializations = [
                    "تقنية المعلومات",
                    "علوم الحاسوب",
                    "هندسة الشبكات",
                    "الأمن السيبراني",
                    "الذكاء الاصطناعي",
                    "علم البيانات",
                    "نظم المعلومات",
                    "الهندسة",
                    "الهندسة المدنية",
                    "الهندسة الكهربائية",
                    "هندسة الاتصالات",
                    "إدارة الأعمال",
                    "المحاسبة",
                    "القانون",
                    "الطب",
                    "الصيدلة",
                    "طب الأسنان",
                    "العلوم",
                    "اللغة العربية",
                    "اللغة الإنجليزية",
                ]

                query = text.casefold()
                matches = [
                    item for item in specializations
                    if query in item.casefold()
                ]

                if not matches:
                    state["stage"] = "specialization"
                    await self._api_call(
                        client,
                        "sendMessage",
                        {
                            "chat_id": chat_id,
                            "text": (
                                "🔎 لم يتم العثور على تخصص مطابق.\\n\\n"
                                "جرّب كلمة أخرى."
                            ),
                            "reply_markup": {
                                "inline_keyboard": [
                                    [
                                        {"text": "🔎 بحث مرة أخرى", "callback_data": "specialization_search"}
                                    ],
                                    [
                                        {"text": "🎓 عرض التخصصات", "callback_data": "request_add_specialization"}
                                    ],
                                ]
                            }
                        }
                    )
                    return

                state["stage"] = "specialization"

                keyboard = [
                    [
                        {
                            "text": f"🎓 {item}",
                            "callback_data": f"specialization:{item}"
                        }
                    ]
                    for item in matches
                ]

                keyboard.append([
                    {"text": "🔎 بحث مرة أخرى", "callback_data": "specialization_search"}
                ])
                keyboard.append([
                    {"text": "⏭️ بدون تخصص", "callback_data": "specialization:none"}
                ])

                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": (
                            f"🔎 <b>نتائج البحث عن:</b> {text}\\n\\n"
                            "اختر التخصص المناسب:"
                        ),
                        "parse_mode": "HTML",
                        "reply_markup": {"inline_keyboard": keyboard}
                    }
                )
                return

            if stage == "deadline_input" and text:
                from datetime import datetime, timezone

                if text == "لا يوجد":
                    state["deadline"] = None
                else:
                    try:
                        state["deadline"] = datetime.strptime(
                            text, "%Y-%m-%d"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        await self._api_call(
                            client,
                            "sendMessage",
                            {
                                "chat_id": chat_id,
                                "text": "⚠️ التاريخ غير صحيح. استخدم الصيغة: YYYY-MM-DD"
                            }
                        )
                        return

                state["stage"] = "confirm"

                specialization = state.get("specialization") or "لا يوجد"
                deadline = state.get("deadline")
                deadline_text = deadline.strftime("%Y-%m-%d") if deadline else "لا يوجد"

                summary = (
                    "📋 <b>مراجعة الطلب</b>\\n\\n"
                    f"<b>العنوان:</b> {state.get('title', '-')}\\n\\n"
                    f"<b>الوصف:</b> {state.get('description', '-')}\\n\\n"
                    f"<b>التخصص:</b> {specialization}\\n\\n"
                    f"<b>الموعد النهائي:</b> {deadline_text}\\n\\n"
                    "هل تريد إرسال الطلب؟"
                )

                await self._api_call(
                    client,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": summary,
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "✅ تأكيد وإرسال", "callback_data": "request_confirm"}],
                                [{"text": "❌ إلغاء الطلب", "callback_data": "request_cancel"}],
                            ]
                        }
                    }
                )
                return

        if text == "/start" or text.startswith("/start "):
            await self._get_or_create_user(message)
            await self._api_call(
                client,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": _welcome_text(
                        chat.get("first_name"),
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": _main_menu(),
                },
            )
