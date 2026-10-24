"""Tests for sensitive-value redaction in structured application logs."""

from __future__ import annotations

import logging
import sys

from backend.app.core.logging import StructuredFormatter


def test_telegram_bot_token_is_redacted_from_message_and_exception() -> None:
    formatter = StructuredFormatter()
    request_url = "https://api.telegram.org/botconfidential-token/getUpdates"
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Request failed for %s",
        args=(request_url,),
        exc_info=None,
    )
    try:
        raise RuntimeError(f"Request failed for {request_url}")
    except RuntimeError:
        record.exc_info = sys.exc_info()

    formatted = formatter.format(record)

    assert "confidential-token" not in formatted
    assert formatted.count("[REDACTED]") == 2
