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
    monkeypatch.setattr(jwt_module, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_routes, "TelegramClient", FakeTelegramClient)
    FakeTelegramClient.sent = []
    FakeTelegramClient.should_fail = provider_fails

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        user = User(
            username="recovery.member",
            email="recovery@example.test",
            password_hash=hash_password("Original-Passphrase-2026"),
            status="ACTIVE",
            telegram_user_id=987654321,
            language="en",
        )
        session.add(user)
        await session.flush()
        if linked:
            session.add(ExternalIdentity(
                user_id=user.id,
                provider="telegram",
                subject="987654321",
                display_name="Recovery Member",
                linked_at=datetime.now(timezone.utc),
                verified_at=datetime.now(timezone.utc),
            ))
        session.add(UserSession(
            user_id=user.id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ))
        await session.commit()
        user_id = user.id

    async def override_get_db():
        async with factory() as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    return engine, factory, user_id, previous_overrides


async def _request_code():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/api/v1/auth/password-recovery/request",
            json={"identifier": "RECOVERY.MEMBER"},
        )


async def _verify_code(code: str):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/api/v1/auth/password-recovery/verify",
            json={
                "identifier": "recovery@example.test",
                "code": code,
                "new_password": "New-Strong-Passphrase-2026",
            },
        )


def test_password_recovery_uses_verified_telegram_and_revokes_sessions(monkeypatch):
    async def scenario():
        engine, factory, user_id, previous = await _prepare(monkeypatch)
        try:
            requested = await _request_code()
            assert requested.status_code == 202
            assert requested.json()["status"] == "accepted"
            assert len(FakeTelegramClient.sent) == 1
            chat_id, message = FakeTelegramClient.sent[0]
            assert chat_id == 987654321
            code = re.search(r"(?<!\d)(\d{8})(?!\d)", message).group(1)

            async with factory() as session:
                challenge = (await session.execute(select(PasswordRecoveryChallenge))).scalar_one()
                assert challenge.delivery_status == "SENT"
                assert challenge.token_hash != code
                assert challenge.failed_attempts == 0

            verified = await _verify_code(code)
            assert verified.status_code == 200
            assert verified.json()["status"] == "password_reset"
            assert verified.json()["reauthentication_required"] is True

            async with factory() as session:
                user = await session.get(User, user_id)
                assert verify_password("New-Strong-Passphrase-2026", user.password_hash)
                sessions = (await session.execute(select(UserSession).where(UserSession.user_id == user_id))).scalars().all()
                assert sessions and all(item.revoked_at is not None for item in sessions)
                challenge = (await session.execute(select(PasswordRecoveryChallenge))).scalar_one()
                assert challenge.consumed_at is not None
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_does_not_send_to_unlinked_identity(monkeypatch):
    async def scenario():
        engine, _, _, previous = await _prepare(monkeypatch, linked=False)
        try:
            response = await _request_code()
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            assert FakeTelegramClient.sent == []
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_provider_failure_never_activates_code(monkeypatch):
    async def scenario():
        engine, factory, _, previous = await _prepare(monkeypatch, provider_fails=True)
        try:
            response = await _request_code()
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            async with factory() as session:
                challenge = (await session.execute(select(PasswordRecoveryChallenge))).scalar_one()
                assert challenge.delivery_status == "FAILED"
                assert challenge.consumed_at is not None
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_invalid_code_is_limited_and_consumed(monkeypatch):
    async def scenario():
        engine, factory, _, previous = await _prepare(monkeypatch)
        try:
            response = await _request_code()
            assert response.status_code == 202
            for _ in range(5):
                invalid = await _verify_code("00000000")
                assert invalid.status_code == 400
            async with factory() as session:
                challenge = (await session.execute(select(PasswordRecoveryChallenge))).scalar_one()
                assert challenge.failed_attempts == 5
                assert challenge.consumed_at is not None
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_request_is_generic_for_unknown_accounts(monkeypatch):
    async def scenario():
        engine, _, _, previous = await _prepare(monkeypatch)
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/password-recovery/request",
                    json={"identifier": "not-a-real-account@example.test"},
                )
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            assert FakeTelegramClient.sent == []
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_request_is_rate_limited_without_account_enumeration(monkeypatch):
    async def scenario():
        engine, _, _, previous = await _prepare(monkeypatch)
        try:
            responses = [await _request_code() for _ in range(4)]
            assert all(response.status_code == 202 for response in responses)
            assert all(response.json()["status"] == "accepted" for response in responses)
            assert len(FakeTelegramClient.sent) == 3
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def _email_settings():
    return SimpleNamespace(
        telegram_bot_token=SecretStr("test-telegram-token"),
        secret_key=SecretStr("test-secret-key-with-more-than-32-characters"),
        email_smtp_host="smtp.example.test",
        email_smtp_port=587,
        email_smtp_username=None,
        email_smtp_password=None,
        email_smtp_from="no-reply@example.test",
        email_smtp_starttls=True,
        email_smtp_use_ssl=False,
        public_app_url="https://ehteraf-tech.vercel.app",
    )


def test_password_recovery_uses_only_verified_email_and_revokes_sessions(monkeypatch):
    async def scenario():
        from backend.app.api.routes import auth as auth_routes

        engine, factory, user_id, previous = await _prepare(monkeypatch)
        delivered = []

        async def fake_send_email(settings, **kwargs):
            delivered.append(kwargs)

        monkeypatch.setattr(auth_routes, "get_settings", _email_settings)
        monkeypatch.setattr(auth_routes, "send_email", fake_send_email)
        try:
            async with factory() as session:
                session.add(ExternalIdentity(
                    user_id=user_id,
                    provider="email",
                    subject="recovery@example.test",
                    display_name="recovery@example.test",
                    linked_at=datetime.now(timezone.utc),
                    verified_at=datetime.now(timezone.utc),
                ))
                await session.commit()

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                requested = await client.post(
                    "/api/v1/auth/password-recovery/request",
                    json={"identifier": "recovery@example.test", "channel": "email"},
                )
            assert requested.status_code == 202
            assert requested.json()["status"] == "accepted"
            assert len(delivered) == 1
            assert delivered[0]["recipient"] == "recovery@example.test"
            code = re.search(r"(?<!\d)(\d{8})(?!\d)", delivered[0]["text_body"]).group(1)

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                verified = await client.post(
                    "/api/v1/auth/password-recovery/verify",
                    json={
                        "identifier": "recovery@example.test",
                        "channel": "email",
                        "code": code,
                        "new_password": "New-Email-Recovery-2026",
                    },
                )
            assert verified.status_code == 200
            assert verified.json()["status"] == "password_reset"
            async with factory() as session:
                user = await session.get(User, user_id)
                assert verify_password("New-Email-Recovery-2026", user.password_hash)
                sessions = (await session.execute(select(UserSession).where(UserSession.user_id == user_id))).scalars().all()
                assert sessions and all(item.revoked_at is not None for item in sessions)
                challenge = (await session.execute(select(PasswordRecoveryChallenge))).scalar_one()
                assert challenge.consumed_at is not None
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_password_recovery_never_uses_unverified_email(monkeypatch):
    async def scenario():
        from backend.app.api.routes import auth as auth_routes

        engine, _, _, previous = await _prepare(monkeypatch)
        delivered = []

        async def fake_send_email(settings, **kwargs):
            delivered.append(kwargs)

        monkeypatch.setattr(auth_routes, "get_settings", _email_settings)
        monkeypatch.setattr(auth_routes, "send_email", fake_send_email)
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/password-recovery/request",
                    json={"identifier": "recovery@example.test", "channel": "email"},
                )
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            assert delivered == []
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())


def test_signed_in_user_can_verify_email_with_explicit_single_use_link(monkeypatch):
    async def scenario():
        from urllib.parse import urlparse, parse_qs
        from backend.app.api.auth_dependencies import get_current_user
        from backend.app.api.routes import auth as auth_routes

        engine, factory, user_id, previous = await _prepare(monkeypatch)
        delivered = []

        async def fake_send_email(settings, **kwargs):
            delivered.append(kwargs)

        monkeypatch.setattr(auth_routes, "get_settings", _email_settings)
        monkeypatch.setattr(auth_routes, "send_email", fake_send_email)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                requested = await client.post("/api/v1/auth/identity-links/email/challenge")
            assert requested.status_code == 202
            assert len(delivered) == 1
            verification_url = re.search(r"https://\S+", delivered[0]["text_body"]).group(0)
            parsed = urlparse(verification_url)
            token = parse_qs(parsed.query)["token"][0]

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                confirmation = await client.get(parsed.path + "?token=" + token)
                assert confirmation.status_code == 200
                assert confirmation.headers["cache-control"] == "no-store, max-age=0"
                assert confirmation.headers["referrer-policy"] == "no-referrer"
                assert confirmation.headers["x-content-type-options"] == "nosniff"
                assert "frame-ancestors 'none'" in confirmation.headers["content-security-policy"]
                async with factory() as session:
                    assert (await session.execute(select(ExternalIdentity).where(ExternalIdentity.provider == "email"))).scalar_one_or_none() is None
                verified = await client.post(parsed.path, data={"token": token})
                assert verified.status_code == 200
                assert "Email address verified" in verified.text

                replay = await client.post(parsed.path, data={"token": token})
                assert replay.status_code == 400

            async with factory() as session:
                identity = (await session.execute(select(ExternalIdentity).where(ExternalIdentity.provider == "email"))).scalar_one()
                assert identity.user_id == user_id
                assert identity.subject == "recovery@example.test"
        finally:
            app.dependency_overrides = previous
            await engine.dispose()

    asyncio.run(scenario())
