"""PostgreSQL-only concurrency acceptance tests for account lifecycle guards.

Run only against the dedicated disposable database named ``phase_acceptance``:
PHASE_ACCEPTANCE_DATABASE_URL=postgresql+asyncpg://.../phase_acceptance \
    uv run --with alembic --group dev --frozen pytest -q tests/test_postgres_concurrency.py
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.api.routes.admin_users import _protect_last_active_admin
from database.models import Base, Role, User


@pytest.mark.skipif(
    not os.getenv("PHASE_ACCEPTANCE_DATABASE_URL"),
    reason="requires the dedicated disposable PostgreSQL acceptance database",
)
def test_concurrent_admin_deactivation_preserves_one_active_admin() -> None:
    database_url = os.environ["PHASE_ACCEPTANCE_DATABASE_URL"]
    parsed_url = make_url(database_url)
    if (
        parsed_url.get_backend_name() != "postgresql"
        or parsed_url.database != "phase_acceptance"
        or parsed_url.host not in {"127.0.0.1", "localhost", "::1"}
    ):
        raise AssertionError(
            "Refusing schema setup: expected the local disposable PostgreSQL database 'phase_acceptance'."
        )

    async def scenario() -> None:
        engine = create_async_engine(database_url, pool_size=5, max_overflow=0)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            # This database is disposable and explicitly named above; no application DB is used.
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
                await connection.run_sync(Base.metadata.create_all)

            async with factory() as session:
                admin_role = Role(name="admin", description="Acceptance test administrator")
                first = User(username="pg-admin-one", status="ACTIVE", roles=[admin_role])
                second = User(username="pg-admin-two", status="ACTIVE", roles=[admin_role])
                session.add_all([first, second])
                await session.commit()
                first_id, second_id = first.id, second.id
                first.last_seen_at = datetime.now(timezone.utc)
                await session.commit()
                refreshed_last_seen = await session.get(User, first_id)
                assert refreshed_last_seen is not None
                assert refreshed_last_seen.last_seen_at is not None
                assert refreshed_last_seen.last_seen_at.tzinfo is not None

            start = asyncio.Event()

            async def deactivate(target_id):
                async with factory() as session:
                    await start.wait()
                    try:
                        await _protect_last_active_admin(session, target_id)
                        target = await session.get(User, target_id)
                        assert target is not None
                        target.status = "SUSPENDED"
                        await session.commit()
                        return "deactivated"
                    except HTTPException as exc:
                        await session.rollback()
                        assert exc.status_code == 409
                        return "protected"

            tasks = [
                asyncio.create_task(deactivate(first_id)),
                asyncio.create_task(deactivate(second_id)),
            ]
            start.set()
            outcomes = await asyncio.gather(*tasks)
            assert sorted(outcomes) == ["deactivated", "protected"]

            async with factory() as session:
                active_admins = await session.scalar(
                    select(func.count(User.id)).where(
                        User.status == "ACTIVE",
                        User.deleted_at.is_(None),
                        User.roles.any(Role.name == "admin"),
                    )
                )
                assert active_admins == 1
        finally:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
            await engine.dispose()

    asyncio.run(scenario())
