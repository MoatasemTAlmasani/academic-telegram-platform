"""SMTP email delivery for account verification and recovery."""

from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from html import escape
from typing import Any


def email_is_configured(settings: Any) -> bool:
    """Return true only when the SMTP endpoint and sender are configured."""
    host = getattr(settings, "email_smtp_host", None)
    sender = getattr(settings, "email_smtp_from", None)
    username = getattr(settings, "email_smtp_username", None)
    password = getattr(settings, "email_smtp_password", None)
    if not host or not sender:
        return False
    if bool(username) != bool(password):
        return False
    return True


async def send_email(
    settings: Any,
    *,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """Send an email through configured SMTP without blocking the event loop."""
    if not email_is_configured(settings):
        raise RuntimeError("Email delivery is not configured.")

    message = EmailMessage()
    message["From"] = settings.email_smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    def deliver() -> None:
        host = settings.email_smtp_host
        port = int(getattr(settings, "email_smtp_port", 587))
        timeout = 15
        use_ssl = bool(getattr(settings, "email_smtp_use_ssl", False))
        starttls = bool(getattr(settings, "email_smtp_starttls", True))
        context = ssl.create_default_context()
        client_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with client_cls(host, port, timeout=timeout, context=context) if use_ssl else client_cls(host, port, timeout=timeout) as server:
            if not use_ssl and starttls:
                server.starttls(context=context)
            username = getattr(settings, "email_smtp_username", None)
            password = getattr(settings, "email_smtp_password", None)
            if username and password:
                secret = password.get_secret_value() if hasattr(password, "get_secret_value") else str(password)
                server.login(username, secret)
            server.send_message(message)

    await asyncio.to_thread(deliver)
