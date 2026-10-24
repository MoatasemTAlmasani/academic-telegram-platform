"""Logging configuration shared by the application and future workers."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any


_TELEGRAM_BOT_API_URL = re.compile(
    r"(https://api\.telegram\.org/bot)[^/\s\"'<>]+"
)


def _redact_telegram_bot_api_url(value: str) -> str:
    """Remove the bot token from Telegram API URLs before they reach logs."""
    return _TELEGRAM_BOT_API_URL.sub(r"\1[REDACTED]", value)


class StructuredFormatter(logging.Formatter):
    """Render log records as compact JSON for machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_telegram_bot_api_url(record.getMessage()),
        }
        component = getattr(record, "component", None)
        if component:
            payload["component"] = component
        if record.exc_info:
            payload["exception"] = _redact_telegram_bot_api_url(
                self.formatException(record.exc_info)
            )
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure structured application logs once at process startup."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
    # HTTPX includes the full request URL in its INFO logs. Telegram Bot API
    # URLs contain the bot token, so keep those requests out of application logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_component_logger(component: str) -> logging.LoggerAdapter[logging.Logger]:
    """Return a logger adapter that tags records with a subsystem name."""
    return logging.LoggerAdapter(
        logging.getLogger("academic_services_platform"),
        {"component": component},
    )