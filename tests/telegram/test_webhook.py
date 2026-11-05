"""Tests for secure Telegram webhook dispatch."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from backend.app.main import app
from backend.app.api.routes import telegram_webhook


class FakeSettings:
    telegram_webhook_secret = SecretStr("test-webhook-secret")
    telegram_bot_token = SecretStr("test-bot-token")


class FakeRunner:
    received: list[dict] = []

    def __init__(self, _token: SecretStr) -> None:
        pass

    async def process_webhook_update(self, update: dict) -> bool:
        self.received.append(update)
        return True


@pytest.fixture(autouse=True)
def webhook_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeRunner.received = []
    monkeypatch.setattr(telegram_webhook, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(telegram_webhook, "TelegramBotRunner", FakeRunner)


@pytest.mark.anyio
async def test_webhook_rejects_invalid_secret() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            json={"update_id": 1, "message": {}},
        )

    assert response.status_code == 403
    assert FakeRunner.received == []


@pytest.mark.anyio
async def test_webhook_dispatches_valid_update_to_full_runner() -> None:
    update = {
        "update_id": 42,
        "message": {
            "message_id": 5,
            "chat": {"id": 123, "type": "private"},
            "text": "/start",
        },
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
            json=update,
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert FakeRunner.received == [update]


@pytest.mark.anyio
async def test_webhook_rejects_invalid_update_id() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
            json={"update_id": "not-an-integer"},
        )

    assert response.status_code == 400
    assert FakeRunner.received == []
