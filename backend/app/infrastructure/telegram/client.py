"""Async client for the official Telegram Bot API."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import SecretStr


class TelegramAPIError(RuntimeError):
    """Raised when Telegram Bot API returns an unsuccessful response."""


class TelegramClient:
    """Small async wrapper around Telegram Bot API."""

    def __init__(self, token: SecretStr, timeout: float = 15.0) -> None:
        value = token.get_secret_value().strip()
        if not value:
            raise ValueError("Telegram bot token is empty.")
        self.base_url = f"https://api.telegram.org/bot{value}"
        self.timeout = timeout

    async def call(
        self,
        method: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/{method}",
                json=payload or {},
            )
            data = response.json()

        if not data.get("ok"):
            raise TelegramAPIError(
                data.get("description") or "Telegram API request failed."
            )

        return data

    async def get_me(self) -> dict[str, Any]:
        return await self.call("getMe")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        return await self.call("sendMessage", payload)
