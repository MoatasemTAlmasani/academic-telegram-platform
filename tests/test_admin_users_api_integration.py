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
            target = User(id=self.targetmÆÈ‹j◊ù   reactivated = await api_harness.request("POST", f"/api/v1/admin/users/{api_harness.target_id}/lifecycle", json={"action":"reactivate","reason":"Return to service"})
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
        lifecycle = await api_harness.request("POST", f"/api/v1/admin/users/{api_harness.target_id}/lifecycle", json={"action":"demÆÈ‹j◊ù