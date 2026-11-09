"""End-to-end API integration checks using an isolated async SQLite database."""

import asyncio
import csv
import io
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
from database.models.identity import Permission as PermissionRecord
from database.models.security import ExternalIdentity, LoginAttempt
from database.models.notifications import Notification
from database.models.catalog import Category, Service
from database.models.enums import ServiceRequestStatus
from database.models.requests import ServiceRequest


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
            admin_role = Role(
                name="integration_admin",
                description="Isolated API integration-test role",
                permissions=[
                    PermissionRecord(code=value, description=f"Test permission {value}")
                    for value in permissions
                ],
            )
            self.actor.roles = [admin_role]
            session.add_all([self.actor, target, other, customer_role])
            session.add_all([
                UserSession(
                    id=self.session_id,
                    user_id=self.other_id,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ),
                UserSession(
                    id=uuid4(),
                    user_id=self.target_id,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ),
            ])
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


def test_platform_security_center_lists_and_revokes_other_user_sessions(api_harness):
    async def scenario():
        await api_harness.start()
        now = datetime.now(timezone.utc)
        async with api_harness.factory() as session:
            locked_user = await session.get(User, api_harness.target_id)
            suspended_user = await session.get(User, api_harness.other_id)
            locked_user.locked_until = now + timedelta(hours=1)
            suspended_user.status = "SUSPENDED"
            session.add(
                LoginAttempt(
                    username_key="unknown.account",
                    ip_address="203.0.113.9",
                    user_id=None,
                    succeeded=False,
                    attempted_at=now - timedelta(minutes=12),
                )
            )
            await session.commit()

        overview = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/security/overview"
        )
        assert overview.status_code == 200, overview.text
        payload = overview.json()
        assert payload["metrics"]["active_sessions"] == 1
        assert payload["metrics"]["failed_logins_24h"] == 1
        assert payload["metrics"]["locked_accounts"] == 1
        assert payload["metrics"]["suspended_accounts"] == 1
        assert payload["recent_failed_logins"][0]["identity"] == "unknown.account"

        listed = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/security/sessions?status=active"
        )
        assert listed.status_code == 200, listed.text
        session_payload = listed.json()
        assert session_payload["count"] == 1
        assert session_payload["items"][0]["user_name"] == "other.member"
        assert session_payload["items"][0]["can_revoke"] is True
        assert "token" not in session_payload["items"][0]

        revoked = await api_harness.request(
            "POST", f"/api/v1/admin/dashboard/security/sessions/{api_harness.session_id}/revoke"
        )
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["status"] == "revoked"
        async with api_harness.factory() as session:
            stored = await session.get(UserSession, api_harness.session_id)
            assert stored.revoked_at is not None
            assert stored.revoked_reason == "revoked_by_admin"
            audit = (await session.execute(
                select(AuditLog).where(AuditLog.action == "security.session.revoked")
            )).scalar_one()
            assert audit.actor_id == api_harness.actor_id
            assert audit.resource_id == api_harness.session_id

    asyncio.run(scenario())


def test_platform_security_center_cannot_revoke_own_account_session(api_harness):
    async def scenario():
        await api_harness.start()
        own_session_id = uuid4()
        async with api_harness.factory() as session:
            session.add(
                UserSession(
                    id=own_session_id,
                    user_id=api_harness.actor_id,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                )
            )
            await session.commit()
        response = await api_harness.request(
            "POST", f"/api/v1/admin/dashboard/security/sessions/{own_session_id}/revoke"
        )
        assert response.status_code == 409
    asyncio.run(scenario())


def test_platform_security_center_revoke_requires_users_update_permission(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        response = await api_harness.request(
            "POST", f"/api/v1/admin/dashboard/security/sessions/{api_harness.session_id}/revoke"
        )
        assert response.status_code == 403
        async with api_harness.factory() as session:
            stored = await session.get(UserSession, api_harness.session_id)
            assert stored.revoked_at is None
    asyncio.run(scenario())


def test_audit_logs_support_datetime_resource_and_actor_filters(api_harness):
    async def scenario():
        await api_harness.start()
        now = datetime.now(timezone.utc)
        async with api_harness.factory() as session:
            session.add_all([
                AuditLog(
                    actor_id=api_harness.actor_id, action="user.updated", resource_type="user",
                    resource_id=api_harness.target_id, description="Updated target account",
                    event_metadata={"field": "status"}, created_at=now - timedelta(minutes=5),
                ),
                AuditLog(
                    actor_id=api_harness.actor_id, action="service.updated", resource_type="service",
                    description="Updated service", created_at=now - timedelta(days=2),
                ),
            ])
            await session.commit()
        response = await api_harness.request(
            "GET", "/api/v1/admin/audit-logs",
            params={
                "actor_id": str(api_harness.actor_id),
                "resource_type": "user",
                "from_datetime": (now - timedelta(hours=1)).isoformat(),
                "to_datetime": now.isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["action"] == "user.updated"
        assert payload["items"][0]["event_metadata"] == {"field": "status"}

        invalid_range = await api_harness.request(
            "GET", "/api/v1/admin/audit-logs",
            params={
                "from_datetime": now.isoformat(),
                "to_datetime": (now - timedelta(hours=1)).isoformat(),
            },
        )
        assert invalid_range.status_code == 422
    asyncio.run(scenario())


def test_admin_can_create_targeted_and_broadcast_in_app_notifications(api_harness):
    async def scenario():
        await api_harness.start(permissions=("admin:access",))
        targeted = await api_harness.request(
            "POST", "/api/v1/admin/notifications",
            json={"title": "Service update", "message": "Your request has been updated.", "target_user_id": str(api_harness.target_id)},
        )
        assert targeted.status_code == 201, targeted.text
        assert targeted.json()["created"] == 1

        own = await api_harness.request("GET", "/api/v1/notifications/me")
        assert own.status_code == 200
        assert own.json()["total"] == 0

        async with api_harness.factory() as session:
            stored = (await session.execute(select(Notification))).scalars().all()
            assert len(stored) == 1
            assert stored[0].user_id == api_harness.target_id
            assert stored[0].channel == "in_app"
            assert stored[0].status == "SENT"

        broadcast = await api_harness.request(
            "POST", "/api/v1/admin/notifications",
            json={"title": "Platform notice", "message": "Scheduled maintenance notice.", "broadcast": True},
        )
        assert broadcast.status_code == 201, broadcast.text
        assert broadcast.json()["created"] == 3

        own_after = await api_harness.request("GET", "/api/v1/notifications/me")
        assert own_after.status_code == 200
        assert own_after.json()["total"] == 1
        assert own_after.json()["items"][0]["title"] == "Platform notice"

        listing = await api_harness.request("GET", "/api/v1/admin/notifications")
        assert listing.status_code == 200
        assert listing.json()["total"] == 4

        recipients = await api_harness.request("GET", "/api/v1/admin/notifications/recipients")
        assert recipients.status_code == 200
        assert len(recipients.json()["items"]) == 3

        invalid = await api_harness.request(
            "POST", "/api/v1/admin/notifications",
            json={"title": "Bad", "message": "No recipient"},
        )
        assert invalid.status_code == 422
    asyncio.run(scenario())


def test_admin_notifications_require_admin_access(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        response = await api_harness.request("GET", "/api/v1/admin/notifications")
        assert response.status_code == 403
    asyncio.run(scenario())


def test_dashboard_overview_requires_admin_access(api_harness):
    async def scenario():
        await api_harness.start()
        response = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/overview"
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_dashboard_overview_returns_expected_empty_state_for_admin(api_harness):
    async def scenario():
        await api_harness.start(permissions=("admin:access",))
        response = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/overview?period_days=30"
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["period_days"] == 30
        assert set(payload["metrics"]) >= {
            "total_customers",
            "requests_in_period",
            "total_users",
            "total_services",
            "total_requests",
        }
        assert payload["service_options"] == []
        assert payload["requests_by_status"] == []
        assert payload["requests_trend"] == []
        assert payload["requests_by_service"] == []
        assert payload["recent_requests"] == []
        assert payload["recent_activity"] == []
        assert payload["overdue_items"] == []
        assert payload["pending_quotation_items"] == []

    asyncio.run(scenario())


def test_dashboard_overview_hides_request_service_and_audit_details_without_permissions(api_harness):
    async def scenario():
        await api_harness.start(permissions=("admin:access",))
        category_id = uuid4()
        service_id = uuid4()
        async with api_harness.factory() as session:
            category = Category(id=category_id, name="Acceptance category")
            service = Service(
                id=service_id, category_id=category_id, name="Acceptance service"
            )
            request = ServiceRequest(
                customer_id=api_harness.target_id,
                service_id=service_id,
                title="Restricted request detail",
                status=ServiceRequestStatus.NEW,
            )
            audit_event = AuditLog(
                actor_id=api_harness.target_id,
                action="acceptance.test",
                created_at=datetime.now(timezone.utc),
            )
            session.add_all([category, service, request, audit_event])
            await session.commit()

        response = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/overview"
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["metrics"]["total_requests"] is None
        assert payload["metrics"]["requests_in_period"] is None
        assert payload["metrics"]["total_services"] is None
        assert payload["metrics"]["pending_quotations"] is None
        assert payload["alerts"]["overdue_requests"] is None
        assert payload["alerts"]["pending_quotations"] is None
        assert payload["service_options"] == []
        assert payload["requests_by_service"] == []
        assert payload["recent_requests"] == []
        assert payload["recent_activity"] == []
        assert payload["overdue_items"] == []
        assert payload["pending_quotation_items"] == []

    asyncio.run(scenario())


def test_dashboard_overview_applies_period_and_service_filters(api_harness):
    async def scenario():
        await api_harness.start(permissions=("admin:access", "requests:read", "services:read"))
        category_id = uuid4()
        service_one_id = uuid4()
        service_two_id = uuid4()
        now = datetime.now(timezone.utc)
        async with api_harness.factory() as session:
            category = Category(id=category_id, name="Filter acceptance category")
            service_one = Service(
                id=service_one_id,
                category_id=category_id,
                name="Filter acceptance service one",
            )
            service_two = Service(
                id=service_two_id,
                category_id=category_id,
                name="Filter acceptance service two",
            )
            requests = [
                ServiceRequest(
                    customer_id=api_harness.target_id,
                    service_id=service_one_id,
                    title="Recent service one request",
                    status=ServiceRequestStatus.NEW,
                    created_at=now - timedelta(days=2),
                ),
                ServiceRequest(
                    customer_id=api_harness.target_id,
                    service_id=service_two_id,
                    title="Recent service two request",
                    status=ServiceRequestStatus.NEW,
                    created_at=now - timedelta(days=3),
                ),
                ServiceRequest(
                    customer_id=api_harness.target_id,
                    service_id=service_one_id,
                    title="Older service one request",
                    status=ServiceRequestStatus.NEW,
                    created_at=now - timedelta(days=45),
                ),
            ]
            session.add_all([category, service_one, service_two, *requests])
            await session.commit()

        overview = await api_harness.request(
            "GET", "/api/v1/admin/dashboard/overview?period_days=30"
        )
        assert overview.status_code == 200, overview.text
        overview_metrics = overview.json()["metrics"]
        assert overview_metrics["total_requests"] == 3
        assert overview_metrics["requests_in_period"] == 2

        filtered = await api_harness.request(
            "GET",
            f"/api/v1/admin/dashboard/overview?period_days=30&service_id={service_one_id}",
        )
        assert filtered.status_code == 200, filtered.text
        filtered_metrics = filtered.json()["metrics"]
        assert filtered_metrics["total_requests"] == 2
        assert filtered_metrics["requests_in_period"] == 1

    asyncio.run(scenario())


def test_role_assignment_requires_roles_manage(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read", "users:update"))
        response = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.target_id}/role",
            json={"role": "manager"},
        )
        assert response.status_code == 403, response.text

    asyncio.run(scenario())


def test_role_assignment_updates_role_revokes_sessions_and_audits(api_harness):
    async def scenario():
        await api_harness.start(permissions=("roles:manage", "users:read"))
        async with api_harness.factory() as session:
            customer = await session.scalar(select(Role).where(Role.name == "customer"))
            manager = Role(name="manager", description="Operations Manager")
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            target.roles = [customer]
            target_session = UserSession(
                id=uuid4(),
                user_id=target.id,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
            session.add_all([manager, target_session])
            await session.commit()
            target_session_id = target_session.id

        response = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.target_id}/role",
            json={"role": "manager"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["role"]["name"] == "manager"
        assert response.json()["sessions_revoked"] == 1

        async with api_harness.factory() as session:
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            assert [role.name for role in target.roles] == ["manager"]
            revoked = await session.get(UserSession, target_session_id)
            assert revoked.revoked_at is not None
            assert revoked.revoked_reason == "role_changed"
            event = await session.scalar(select(AuditLog).where(AuditLog.resource_id == api_harness.target_id))
            assert event.action == "user.role_assigned"
            assert event.event_metadata["before_roles"] == ["customer"]
            assert event.event_metadata["after_roles"] == ["manager"]

    asyncio.run(scenario())


def test_role_assignment_rejects_unknown_role_and_self_change(api_harness):
    async def scenario():
        await api_harness.start(permissions=("roles:manage",))
        invalid = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.target_id}/role",
            json={"role": "root"},
        )
        assert invalid.status_code == 422, invalid.text

        async with api_harness.factory() as session:
            session.add(Role(name="manager", description="Operations Manager"))
            await session.commit()
        self_change = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.actor_id}/role",
            json={"role": "manager"},
        )
        assert self_change.status_code == 409, self_change.text

    asyncio.run(scenario())


def test_last_active_super_admin_cannot_be_demoted(api_harness):
    async def scenario():
        await api_harness.start(permissions=("roles:manage",))
        async with api_harness.factory() as session:
            super_admin = Role(name="super_admin", description="Super Admin")
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            target.roles = [super_admin]
            session.add(super_admin)
            await session.commit()

        response = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.target_id}/role",
            json={"role": "customer"},
        )
        assert response.status_code == 409, response.text
        assert "last active Super Admin" in response.text

    asyncio.run(scenario())


def test_user_directory_date_filters_and_sorting(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        async with api_harness.factory() as session:
            target = await session.get(User, api_harness.target_id)
            other = await session.get(User, api_harness.other_id)
            target.created_at = datetime(2026, 1, 3, tzinfo=timezone.utc)
            other.created_at = datetime(2026, 1, 4, tzinfo=timezone.utc)
            await session.commit()

        response = await api_harness.request(
            "GET",
            "/api/v1/admin/users",
            params={
                "created_from": "2026-01-03T00:00:00Z",
                "created_to": "2026-01-04T23:59:59Z",
                "sort_by": "username",
                "sort_order": "asc",
            },
        )
        assert response.status_code == 200, response.text
        assert [item["username"] for item in response.json()["items"]] == ["other.member", "target.member"]
        assert response.json()["total"] == 2

        invalid_range = await api_harness.request(
            "GET",
            "/api/v1/admin/users",
            params={"created_from": "2026-02-01T00:00:00Z", "created_to": "2026-01-01T00:00:00Z"},
        )
        assert invalid_range.status_code == 422, invalid_range.text

    asyncio.run(scenario())


def test_super_admin_can_create_privileged_role_when_authorized(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:create", "roles:manage"))
        async with api_harness.factory() as session:
            session.add(Role(name="admin", description="Administrator"))
            await session.commit()

        response = await api_harness.request(
            "POST",
            "/api/v1/admin/users",
            json={
                "username": "new.admin",
                "password": "A-strong-test-password-123",
                "email": "new.admin@example.test",
                "role": "admin",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["roles"][0]["name"] == "admin"

    asyncio.run(scenario())


def test_last_active_super_admin_cannot_be_deactivated(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:update",))
        async with api_harness.factory() as session:
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            session.add(Role(name="super_admin", description="Super Admin"))
            super_admin = await session.scalar(select(Role).where(Role.name == "super_admin"))
            if super_admin is None:
                await session.flush()
                super_admin = await session.scalar(select(Role).where(Role.name == "super_admin"))
            target.roles = [super_admin]
            await session.commit()

        response = await api_harness.request(
            "POST",
            f"/api/v1/admin/users/{api_harness.target_id}/lifecycle",
            json={"action": "deactivate", "reason": "Protect final Super Admin"},
        )
        assert response.status_code == 409, response.text
        assert "last active Super Admin" in response.text

    asyncio.run(scenario())


def test_super_admin_bootstrap_requires_exact_account_and_records_audit(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        from scripts.bootstrap_super_admin import bootstrap_super_admin

        async with api_harness.factory() as session:
            session.add(Role(name="super_admin", description="Super Admin"))
            await session.commit()
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            with pytest.raises(ValueError, match="confirmation username"):
                await bootstrap_super_admin(
                    session,
                    user_id=target.id,
                    confirmed_username="wrong.username",
                    operator="approved-operator",
                    reason="Initial platform administrator bootstrap",
                )
            await session.rollback()

            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == api_harness.target_id)
            )
            target_session = UserSession(
                id=uuid4(),
                user_id=target.id,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
            session.add(target_session)
            await session.commit()
            session_id = target_session.id

            result = await bootstrap_super_admin(
                session,
                user_id=target.id,
                confirmed_username="target.member",
                operator="approved-operator",
                reason="Initial platform administrator bootstrap",
            )
            assert result["after_roles"] == ["super_admin"]
            assert result["sessions_revoked"] == 1
            target = await session.scalar(
                select(User).options(selectinload(User.roles)).where(User.id == target.id)
            )
            assert [role.name for role in target.roles] == ["super_admin"]
            revoked = await session.get(UserSession, session_id)
            await session.refresh(revoked)
            assert revoked.revoked_at is not None
            event = await session.scalar(
                select(AuditLog).where(AuditLog.action == "user.role_bootstrapped")
            )
            assert event.actor_id is None
            assert event.event_metadata["operator"] == "approved-operator"
            assert event.event_metadata["reason"] == "Initial platform administrator bootstrap"

            with pytest.raises(ValueError, match="already exists"):
                await bootstrap_super_admin(
                    session,
                    user_id=api_harness.other_id,
                    confirmed_username="other.member",
                    operator="approved-operator",
                    reason="Attempt second bootstrap",
                )

    asyncio.run(scenario())


def test_admin_password_recovery_uses_verified_channel_and_is_audited(api_harness, monkeypatch):
    from backend.app.api.routes import auth as auth_routes
    monkeypatch.setattr(auth_routes, "_get_secret_key", lambda: "isolated-test-secret")

    async def scenario():
        await api_harness.start(permissions=("users:update",))
        response = await api_harness.request(
            "POST",
            f"/api/v1/admin/users/{api_harness.target_id}/password-recovery",
        )
        assert response.status_code == 202, response.text
        assert response.json()["status"] == "accepted"
        assert "verified recovery channel" in response.json()["message"]

        async with api_harness.factory() as session:
            event = await session.scalar(
                select(AuditLog).where(
                    AuditLog.action == "user.password_recovery_requested_by_admin",
                    AuditLog.resource_id == api_harness.target_id,
                )
            )
            assert event is not None
            assert event.actor_id == api_harness.actor_id
            assert event.event_metadata["channel"] == "telegram"

    asyncio.run(scenario())


def test_admin_password_recovery_requires_users_update(api_harness):
    async def scenario():
        await api_harness.start(permissions=("users:read",))
        denied = await api_harness.request(
            "POST",
            f"/api/v1/admin/users/{api_harness.target_id}/password-recovery",
        )
        assert denied.status_code == 403, denied.text

    asyncio.run(scenario())

def test_account_and_activity_csv_exports_neutralize_spreadsheet_formulas(api_harness):
    async def scenario():
        await api_harness.start()
        formula = '=HYPERLINK("https://evil.test","click")'
        phone_formula = "+CMD|' /C calc'!A0"
        async with api_harness.factory() as session:
            target = await session.get(User, api_harness.target_id)
            target.first_name = formula
            target.phone = phone_formula
            session.add(AuditLog(
                actor_id=api_harness.actor_id,
                action="user.profile_note",
                resource_type="user",
                resource_id=api_harness.target_id,
                description=formula,
                event_metadata={},
                created_at=datetime.now(timezone.utc),
            ))
            await session.commit()

        directory = await api_harness.request("GET", "/api/v1/admin/users/export.csv")
        assert directory.status_code == 200, directory.text
        directory_rows = list(csv.reader(io.StringIO(directory.text.lstrip("\ufeff"))))
        target_row = next(row for row in directory_rows if row[1] == "target.member")
        assert target_row[3] == "'" + formula
        assert target_row[5] == "'" + phone_formula

        activity = await api_harness.request(
            "GET", f"/api/v1/admin/users/{api_harness.target_id}/activity.csv"
        )
        assert activity.status_code == 200, activity.text
        activity_rows = list(csv.reader(io.StringIO(activity.text.lstrip("\ufeff"))))
        event_row = next(row for row in activity_rows if row[-1] == "'" + formula)
        assert event_row[-1] == "'" + formula

    asyncio.run(scenario())


def test_changing_account_email_invalidates_previous_verified_email_identity(api_harness):
    async def scenario():
        await api_harness.start()
        async with api_harness.factory() as session:
            session.add(ExternalIdentity(
                user_id=api_harness.target_id,
                provider="email",
                subject="target@example.test",
                display_name="target@example.test",
                linked_at=datetime.now(timezone.utc),
                verified_at=datetime.now(timezone.utc),
            ))
            await session.commit()

        response = await api_harness.request(
            "PATCH",
            f"/api/v1/admin/users/{api_harness.target_id}",
            json={"email": "new.target@example.test"},
        )
        assert response.status_code == 200, response.text
        async with api_harness.factory() as session:
            identities = (await session.execute(
                select(ExternalIdentity).where(
                    ExternalIdentity.user_id == api_harness.target_id,
                    ExternalIdentity.provider == "email",
                )
            )).scalars().all()
            assert identities == []

    asyncio.run(scenario())


def test_custom_role_can_be_created_audited_and_assigned_with_session_revocation(api_harness):
    async def scenario():
        await api_harness.start(permissions=("roles:manage",))
        created = await api_harness.request(
            "POST",
            "/api/v1/rbac/roles",
            json={
                "name": "  REGIONAL_MANAGER  ",
                "description": " Regional operations ",
            },
        )
        assert created.status_code == 201, created.text
        role = created.json()["role"]
        assert role["name"] == "regional_manager"
        assert role["description"] == "Regional operations"
        assert role["permissions"] == []

        updated = await api_harness.request(
            "PATCH",
            f"/api/v1/rbac/roles/{role['id']}",
            json={
                "name": " AREA_LEAD ",
                "description": " Area operations ",
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["role"]["name"] == "area_lead"
        assert updated.json()["role"]["description"] == "Area operations"

        duplicated = await api_harness.request(
            "POST",
            f"/api/v1/rbac/roles/{role['id']}/duplicate",
            json={
                "name": "AREA_LEAD_COPY",
                "description": "Area operations copy",
            },
        )
        assert duplicated.status_code == 201, duplicated.text
        assert duplicated.json()["role"]["name"] == "area_lead_copy"
        assert duplicated.json()["role"]["description"] == "Area operations copy"

        assigned = await api_harness.request(
            "PUT",
            f"/api/v1/admin/users/{api_harness.target_id}/role",
            json={"role": "area_lead_copy"},
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["role"]["name"] == "area_lead_copy"
        assert assigned.json()["sessions_revoked"] == 1

        async with api_harness.factory() as session:
            target = await session.get(User, api_harness.target_id, options=[selectinload(User.roles)])
            assert [item.name for item in target.roles] == ["area_lead_copy"]
            active_sessions = (await session.execute(
                select(UserSession).where(
                    UserSession.user_id == api_harness.target_id,
                    UserSession.revoked_at.is_(None),
                )
            )).scalars().all()
            assert active_sessions == []
            events = (await session.execute(
                select(AuditLog).order_by(AuditLog.created_at.asc())
            )).scalars().all()
            assert {event.action for event in events} == {
                "rbac.role_created",
                "rbac.role_updated",
                "rbac.role_duplicated",
                "user.role_assigned",
            }

    asyncio.run(scenario())
