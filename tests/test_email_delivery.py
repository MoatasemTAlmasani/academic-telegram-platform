"""Tests for safe optional SMTP configuration."""

import asyncio
from types import SimpleNamespace

from pydantic import SecretStr

from backend.app.infrastructure.email.client import email_is_configured, send_email


def _settings(**overrides):
    values = {
        "email_smtp_host": "smtp.example.test",
        "email_smtp_port": 587,
        "email_smtp_username": None,
        "email_smtp_password": None,
        "email_smtp_from": "no-reply@example.test",
        "email_smtp_starttls": True,
        "email_smtp_use_ssl": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_email_delivery_is_configured_for_anonymous_smtp_relay():
    assert email_is_configured(_settings())


def test_blank_secret_environment_value_is_treated_as_absent():
    settings = _settings(email_smtp_password=SecretStr(""))
    assert email_is_configured(settings)


def test_smtp_username_and_password_must_be_configured_together():
    assert not email_is_configured(_settings(email_smtp_username="mailer"))
    assert not email_is_configured(
        _settings(email_smtp_password=SecretStr("secret-password"))
    )


def test_smtp_host_and_sender_must_be_nonempty():
    assert not email_is_configured(_settings(email_smtp_host="  "))
    assert not email_is_configured(_settings(email_smtp_from=""))


def test_send_email_refuses_unconfigured_delivery():
    async def scenario():
        try:
            await send_email(
                _settings(email_smtp_host=None),
                recipient="user@example.test",
                subject="Test",
                text_body="Test message",
            )
        except RuntimeError as error:
            assert "not configured" in str(error)
        else:
            raise AssertionError("Unconfigured SMTP delivery must be rejected.")

    asyncio.run(scenario())
