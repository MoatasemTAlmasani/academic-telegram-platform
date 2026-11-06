"""Isolated tests for verified-Telegram password recovery."""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.api.dependencies import get_db
from backend.app.main import app
from database.models import Base, ExternalIdentity, PasswordRecoveryChallenge, User, UserSession
from backend.app.modules.authentication.passwords import hash_password, verify_password


class FakeTelegramClient:
    sent: list[tuple[int, str]] = []
    should_fail = False

    def __init__(self, token):
        assert token.get_secret_value() == "test-telegram-token"

    async def send_message(self, chat_id: int, text: str):
        if self.should_fail:
            raise RuntimeError("simulated provider failure")
        self.sent.append((chat_id, text))
        return {"ok": True}


async def _prepare(monkeypatch, *, linked: bool = True, provider_fails: bool = False):
    from backend.app.api.routes import auth as auth_routes
    from backend.app.modules.authentication import jwt as jwt_module

    settings = SimpleNamespace(
        telegram_bot_token=SecretStr("test-telegram-token"),
        secret_key=SecretStr("test-secret-key-with-more-than-32-characters"),
    )
    monkeypatch.setattr(auth_routes, "get_settings", lambda: settings)
    monkeypatch.setattr(jwt_module, "mÆÈ‹j◊ù