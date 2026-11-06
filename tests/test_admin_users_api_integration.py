"""End-to-end API integration checks using an isolated async SQLite database."""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.infrastructure.persistence.database import get_session
from backend.app.main import app
from database.models import Base, AuditLog, Role, User, UserSession


class AdminApiHarness:
    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.actor_id = uuid4()
        self.target_id = uuid4()
        self.other_id = uuid4()
        self.session_id = uuid4()
        self.actor = None
        self.previous_overrides = app.dependency_overrides.copy()

    async def start(self, permissions=("users:read", "users:update", "users:create", "users:delete", "audit:read")):
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with self.factory() as session:
            self.actor = User(id=self.actor_id, username="integration.admin", email="admin@example.test", status="ACTIVE")
            target = User(id=self.target_id, username="target.member", email="target@example.test", status="ACTIVE")
            other = User(id=self.other_id, username="other.member", email="other@example.test", status="ACTIVE")
            customer_role = Role(name="customer", description="Customer account")
            session.add_all([self.actor, target, other, customer_role])
            session.add(UserSession(
                id=self.session_id,
                user_id=self.other_id,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ))
            await session.commit()

        current_user = SimpleNamespace(
            id=self.actor_id,
            roles=[SimpleNamespace(permissions=[SimpleNamespace(code=value) for value in permissions])],
        )

        async def override_get_session():
            async with self.factory() as session:
                yield session

        async def override_current_user():
            return current_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_current_user] = override_current_user
        return current_user

    async def request(self, method, path, **kwargs):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    async def close(self):
        app.dependency_overrides = self.previous_overrides
        await self.engine.dispose()


@pytest.fixture
def api_harness():
    harness = AdminApiHarness()
    yield harness
    asyncio.run(harness.close())


def test_admin_user_list_requires_permission_and_returns_safe_directory(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        response = await api_harness.request("GET", "/api/v1/admin/users?page=1&page_size=10")
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 3
        assert {item["username"] for item in payload["items"]} == {
            "integration.admin", "target.member", "other.member"
        }
        assert all("password_hash" not in item for item in payload["items"])

    asyncio.run(scenario())


def test_admin_user_list_denies_missing_rbac_permission(api_harness):
    async def scenario():
        await api_harness.start(permissions=("audit:read",))
        response = await api_harness.request("GET", "/api/v1/admin/users")
        assert response.status_code == 403

    asyncio.run(scenario())


def test_cross_account_session_revocation_is_not_found_and_changes_nothing(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request(
            "DELETE",
            f"/api/v1/admin/users/{api_harness.target_id}/sessions/{api_harness.session_id}",
        )
        assert response.status_code == 404
        async with api_harness.factory() as session:
            stored = await session.get(UserSession, api_harness.session_id)
            assert stored is not None
            assert stored.user_id == api_harness.other_id
            assert stored.revoked_at is None
            assert (await session.execute(select(AuditLog))).scalars().all() == []

    asyncio.run(scenario())


def test_lifecycle_deactivation_revokes_sessions_and_writes_audit_atomically(api_harness):
    async def scenario():
        await api_harness.start()
        async with api_harness.factory() as session:
            session.add(UserSession(
                user_id=api_harness.target_id,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ))
            await session.commit()

        response = await api_harness.request(
            "POST",
            f"/api/v1/admin/users/{api_harness.target_id}/lifecycle",
            json={"action": "deactivate", "reason": "Approved account closure"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "INACTIVE"
        assert response.json()["revoked_sessions"] == 1

        async with api_harness.factory() as session:
            target = await session.get(User, api_harness.target_id)
            assert target.status == "INACTIVE"
            sessions = (await session.execute(select(UserSession).where(UserSession.user_id == api_harness.target_id))).scalars().all()
            assert len(sessions) == 1 and sessions[0].revoked_at is not None
            events = (await session.execute(select(AuditLog).where(AuditLog.resource_id == api_harness.target_id))).scalars().all()
            assert len(events) == 1
            assert events[0].action == "user.lifecycle_changed"

    asyncio.run(scenario())


def test_missing_account_lifecycle_returns_404_without_audit(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request(
            "POST",
            f"/api/v1/admin/users/{uuid4()}/lifecycle",
            json={"action": "deactivate", "reason": "Approved account closure"},
        )
        assert response.status_code == 404
        async with api_harness.factory() as session:
            assert (await session.execute(select(AuditLog))).scalars().all() == []

    asyncio.run(scenario())

def test_account_creation_returns_safe_representation_and_audit(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request("POST", "/api/v1/admin/users", json={"username":"new.customer","password":"A-strong-test-password-123","email":"NEW.CUSTOMER@example.test","first_name":"New","role":"customer"})
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["email"] == "new.customer@example.test"
        assert "password_hash" not in payload and "password" not in payload
        async with api_harness.factory() as session:
            created = await session.scalar(select(User).where(User.username == "new.customer"))
            assert created is not None and created.password_hash != "A-strong-test-password-123"
            event = await session.scalar(select(AuditLog).where(AuditLog.resource_id == created.id))
            assert event is not None and event.action == "user.created"
            assert "password" not in str(event.event_metadata).lower()
    asyncio.run(scenario())

def test_account_creation_rejects_duplicate_and_privileged_role(api_harness):
    async def scenario():
        await api_harness.start()
        duplicate = await api_harness.request("POST", "/api/v1/admin/users", json={"username":"target.member","password":"A-strong-test-password-123"})
        assert duplicate.status_code == 409
        escalation = await api_harness.request("POST", "/api/v1/admin/users", json={"username":"attempt.admin","password":"A-strong-test-password-123","role":"admin"})
        assert escalation.status_code == 403
        invalid = await api_harness.request("POST", "/api/v1/admin/users", json={"username":"ab","password":"short"})
        assert invalid.status_code == 422
        async with api_harness.factory() as session:
            assert (await session.execute(select(AuditLog))).scalars().all() == []
    asyncio.run(scenario())

def test_account_update_persists_safe_before_after_audit(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request("PATCH", f"/api/v1/admin/users/{api_harness.target_id}", json={"first_name":"Updated","phone":"+967700000001"})
        assert response.status_code == 200, response.text
        assert response.json()["first_name"] == "Updated"
        assert "password_hash" not in response.json()
        async with api_harness.factory() as session:
            event = await session.scalar(select(AuditLog).where(AuditLog.resource_id == api_harness.target_id))
            assert event.action == "user.updated"
            assert event.event_metadata["before"]["first_name"] is None
            assert event.event_metadata["after"]["first_name"] == "Updated"
            assert "password" not in str(event.event_metadata).lower()
    asyncio.run(scenario())

def test_account_update_rejects_role_escalation_without_audit(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request("PATCH", f"/api/v1/admin/users/{api_harness.target_id}", json={"role":"admin"})
        assert response.status_code == 403
        async with api_harness.factory() as session:
            assert (await session.execute(select(AuditLog))).scalars().all() == []
    asyncio.run(scenario())

def test_lifecycle_reactivation_and_archive_session_scoping(api_harness):
    async def scenario():
        await api_harness.start()
        async with api_harness.factory() as session:
            target_session_id = uuid4()
            session.add(UserSession(id=target_session_id,user_id=api_harness.target_id,created_at=datetime.now(timezone.utc),expires_at=datetime.now(timezone.utc)+timedelta(days=1)))
            await session.commit()
        deactivated = await api_harness.request("POST", f"/api/v1/admin/users/{api_harness.target_id}/lifecycle", json={"action":"deactivate","reason":"Temporary leave"})
        assert deactivated.status_code == 200, deactivated.text
        async with api_harness.factory() as session:
            assert (await session.get(UserSession,target_session_id)).revoked_at is not None
            assert (await session.get(UserSession,api_harness.session_id)).revoked_at is None
        reactivated = await api_harness.request("POST", f"/api/v1/admin/users/{api_harness.target_id}/lifecycle", json={"action":"reactivate","reason":"Return to service"})
        assert reactivated.status_code == 200 and reactivated.json()["status"] == "ACTIVE"
        archived = await api_harness.request("DELETE", f"/api/v1/admin/users/{api_harness.target_id}", params={"reason":"Account closure requested"})
        assert archived.status_code == 204, archived.text
        async with api_harness.factory() as session:
            target = await session.get(User,api_harness.target_id)
            assert target.deleted_at is not None
            actions = (await session.execute(select(AuditLog.action).where(AuditLog.resource_id == api_harness.target_id))).scalars().all()
            assert actions.count("user.lifecycle_changed") == 2 and "user.archived" in actions
    asyncio.run(scenario())

def test_last_active_admin_cannot_be_deactivated_or_archived(api_harness):
    async def scenario():
        await api_harness.start()
        async with api_harness.factory() as session:
            admin_role = Role(name="admin",description="Administrator")
            target = await session.scalar(select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id))
            target.roles.append(admin_role)
            await session.commit()
        lifecycle = await api_harness.request("POST", f"/api/v1/admin/users/{api_harness.target_id}/lifecycle", json={"action":"deactivate","reason":"Test final admin guard"})
        assert lifecycle.status_code == 409, lifecycle.text
        archive = await api_harness.request("DELETE", f"/api/v1/admin/users/{api_harness.target_id}", params={"reason":"Test final admin guard"})
        assert archive.status_code == 409, archive.text
        async with api_harness.factory() as session:
            target = await session.get(User,api_harness.target_id)
            assert str(target.status).upper() == "ACTIVE" and target.deleted_at is None
            assert (await session.execute(select(AuditLog))).scalars().all() == []
    asyncio.run(scenario())
