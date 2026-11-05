"""Regression tests for Telegram request description and specialization steps."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import SecretStr

from backend.app.infrastructure.telegram.bot_runner import (
    TelegramBotRunner,
    _normalize_request_deadline,
)


CHAT_ID = 184_200_501
SERVICE_ID = "a3e25f15-65ad-47eb-88d3-a1b2ce6a1399"


class FakeTelegramAPI:
    """Capture Telegram requests and return realistic sendMessage results."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._message_id = 100

    async def __call__(
        self,
        _client: Any,
        method: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = payload or {}
        self.calls.append((method, payload))
        if method == "sendMessage":
            self._message_id += 1
            return {"ok": True, "result": {"message_id": self._message_id}}
        return {"ok": True, "result": True}

    def last_sent_message(self) -> dict[str, Any]:
        return next(
            payload
            for method, payload in reversed(self.calls)
            if method == "sendMessage"
        )


@pytest.fixture
def bot_and_api(monkeypatch: pytest.MonkeyPatch) -> tuple[TelegramBotRunner, FakeTelegramAPI]:
    bot = TelegramBotRunner(SecretStr("test-token"))
    fake_api = FakeTelegramAPI()
    monkeypatch.setattr(bot, "_api_call", fake_api)
    return bot, fake_api


def callback(data: str, callback_id: str = "callback-1") -> dict[str, Any]:
    return {
        "id": callback_id,
        "data": data,
        "from": {"id": CHAT_ID, "first_name": "Test"},
        "message": {
            "message_id": 50,
            "chat": {"id": CHAT_ID, "type": "private"},
        },
    }


async def start_request(bot: TelegramBotRunner) -> None:
    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback(f"request:{SERVICE_ID}", "request-start"),
    )


async def start_description_input(
    bot: TelegramBotRunner,
) -> int:
    await start_request(bot)
    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("request_add_description", "description-start"),
    )
    return bot._conversation_state[CHAT_ID]["expected_prompt_message_id"]


def private_message(
    text: str,
    *,
    message_id: int,
    reply_to_message_id: int | None,
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "message_id": message_id,
        "chat": {"id": CHAT_ID, "type": "private"},
        "from": {"id": CHAT_ID, "first_name": "Test"},
        "text": text,
    }
    if reply_to_message_id is not None:
        message["reply_to_message"] = {"message_id": reply_to_message_id}
    return message


@pytest.mark.anyio
async def test_description_reply_transitions_and_preserves_request_data(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, fake_api = bot_and_api
    prompt_id = await start_description_input(bot)

    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "تحليل بيانات الاستبيان",
            message_id=101,
            reply_to_message_id=prompt_id,
        ),
    )

    state = bot._conversation_state[CHAT_ID]
    assert state["stage"] == "specialization"
    assert state["service_id"] == SERVICE_ID
    assert state["description"] == "تحليل بيانات الاستبيان"
    assert "specialization" not in state

    keyboard = fake_api.last_sent_message()["reply_markup"]["inline_keyboard"]
    assert keyboard[0][0]["callback_data"] == "request_add_specialization"


@pytest.mark.anyio
async def test_specialization_button_search_and_selection_complete_step(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, _ = bot_and_api
    prompt_id = await start_description_input(bot)
    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "تحليل بيانات الاستبيان",
            message_id=101,
            reply_to_message_id=prompt_id,
        ),
    )
    state = bot._conversation_state[CHAT_ID]

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("request_add_specialization", "show-specializations"),
    )
    assert state["stage"] == "specialization"

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("specialization_search", "search-specialization"),
    )
    search_prompt_id = state["expected_prompt_message_id"]
    assert state["stage"] == "specialization_search_input"

    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "علوم الحاسوب",
            message_id=102,
            reply_to_message_id=search_prompt_id,
        ),
    )
    assert state["stage"] == "specialization"

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("specialization:علوم الحاسوب", "select-specialization"),
    )

    assert state["stage"] == "deadline"
    assert state["service_id"] == SERVICE_ID
    assert state["description"] == "تحليل بيانات الاستبيان"
    assert state["specialization"] == "علوم الحاسوب"


@pytest.mark.anyio
async def test_unrelated_text_does_not_become_description(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, _ = bot_and_api
    prompt_id = await start_description_input(bot)
    state = bot._conversation_state[CHAT_ID]

    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "رسالة غير مرتبطة",
            message_id=101,
            reply_to_message_id=None,
        ),
    )

    assert state["stage"] == "description_input"
    assert state.get("description") is None
    assert state["expected_prompt_message_id"] == prompt_id

    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "الوصف الصحيح",
            message_id=102,
            reply_to_message_id=prompt_id,
        ),
    )
    assert state["stage"] == "specialization"
    assert state["description"] == "الوصف الصحيح"


@pytest.mark.anyio
async def test_empty_search_results_allow_retry(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, _ = bot_and_api
    prompt_id = await start_description_input(bot)
    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message("وصف", message_id=101, reply_to_message_id=prompt_id),
    )
    state = bot._conversation_state[CHAT_ID]

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("specialization_search", "search-1"),
    )
    search_prompt_id = state["expected_prompt_message_id"]
    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message(
            "غير موجود",
            message_id=102,
            reply_to_message_id=search_prompt_id,
        ),
    )

    assert state["stage"] == "specialization"
    assert state["description"] == "وصف"
    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("specialization_search", "search-retry"),
    )
    assert state["stage"] == "specialization_search_input"


@pytest.mark.anyio
async def test_new_or_repeated_request_callback_does_not_erase_active_request(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, _ = bot_and_api
    prompt_id = await start_description_input(bot)
    await bot._handle_message(
        None,  # type: ignore[arg-type]
        private_message("وصف محفوظ", message_id=101, reply_to_message_id=prompt_id),
    )
    state = bot._conversation_state[CHAT_ID]

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("request:another-service", "stale-request-button"),
    )

    assert bot._conversation_state[CHAT_ID] is state
    assert state["stage"] == "specialization"
    assert state["service_id"] == SERVICE_ID
    assert state["description"] == "وصف محفوظ"


@pytest.mark.anyio
async def test_duplicate_update_id_is_processed_only_once(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, _ = bot_and_api
    repeated_update = {
        "update_id": 700,
        "callback_query": callback(f"request:{SERVICE_ID}", "same-update"),
    }

    await bot._handle_update(None, repeated_update)  # type: ignore[arg-type]
    original_state = bot._conversation_state[CHAT_ID]
    original_state["description"] = "يبقى محفوظًا"
    original_state["stage"] = "specialization"

    await bot._handle_update(None, repeated_update)  # type: ignore[arg-type]

    assert bot._conversation_state[CHAT_ID] is original_state
    assert original_state["description"] == "يبقى محفوظًا"
    assert original_state["stage"] == "specialization"


@pytest.mark.anyio
async def test_specialization_button_with_missing_session_is_safe(
    bot_and_api: tuple[TelegramBotRunner, FakeTelegramAPI],
) -> None:
    bot, fake_api = bot_and_api

    await bot._handle_callback_query(
        None,  # type: ignore[arg-type]
        callback("request_add_specialization", "missing-session"),
    )

    assert CHAT_ID not in bot._conversation_state
    assert "انتهت جلسة الطلب" in fake_api.last_sent_message()["text"]



def test_request_deadline_date_string_is_normalized_to_utc_datetime() -> None:
    deadline = _normalize_request_deadline("2026-11-30")

    assert deadline == datetime(2026, 11, 30, tzinfo=timezone.utc)
    assert deadline.tzinfo is timezone.utc


def test_request_deadline_datetime_is_preserved() -> None:
    deadline = datetime(2026, 11, 30, 12, 30, tzinfo=timezone.utc)

    assert _normalize_request_deadline(deadline) is deadline


def test_request_deadline_none_remains_none() -> None:
    assert _normalize_request_deadline(None) is None


def test_invalid_request_deadline_is_rejected() -> None:
    with pytest.raises(ValueError):
        _normalize_request_deadline("not-a-date")
