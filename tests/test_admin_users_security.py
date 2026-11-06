"""Authorization, tenant-target scoping, and concurrency guards for Module 02."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import update

from backend.app.api.routes import admin_users
from backend.app.api.rbac_dependencies import require_permission
from backend.app.modules.authentication.permissions import Permission
from database.models.identity import UserSession


class _Result:
    def __init__(self, value=None, *, rowcount=0):
        self.value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class _Session:
    def __init__(self, results=()):
        self.results = list(results)
        self.statements = []
        self.added = []
        self.committed = False

    async def execute(self, statement):
        self.statements.append(statement)
        if self.results:
            result = self.results.pop(0)
            return result
        return _Result()

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.committed = True


def _dependency_tree(dependencies):
    for dependency in dependencies:
        yield dependency
        yield from _dependency_tree(dependency.dependencies)


def test_every_admin_user_route_requires_authentication_and_rbac_permission():
    routes = [route for route in admin_users.router.routes if isinstance(route, APIRoute)]
    assert routes

    for route in routes:
        dependencies = list(_dependency_tree(route.dependant.dependencies))
        calls = [dependency.call for dependency in dependencies]
        assert any(call is not None and call.__name__ == "permission_dependency" for call in calls), (
            f"{route.methods} {route.path} is missing a permission dependency"
        )
        assert any(call is admin_users.get_current_user for call in calls), (
            f"{route.methods} {route.path} is missing authenticated-user enforcement"
        )


def test_permission_dependency_denies_user_without_required_permission():
    dependency = require_permission(Permission.USERS_READ)
    user = SimpleNamespace(roles=[SimpleNamespace(permissions=[])])

    async def run():
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=user)
        assert exc_info.value.status_code == 403

    asyncio.run(run())


def test_permission_dependency_accepts_exact_granted_permission():
    dependency = require_permission(Permission.USERS_READ)
    user = SimpleNamespace(
        roles=[SimpleNamespace(permissions=[SimpleNamespace(code=Permission.USERS_READ.value)])]
    )

    assert asyncio.run(dependency(current_user=user)) is user


def test_revoking_session_from_another_user_is_not_found():
    actor_id, owner_id, other_user_id, session_id = uuid4(), uuid4(), uuid4(), uuid4()
    session = _Session([_Result(None)])

    async def run():
        with pytest.raises(HTTPException) as exc_info:
            await admin_users.revoke_admin_user_session(
                user_id=other_user_id,
                session_id=session_id,
                current_user=SimpleNamespace(id=actor_id),
                session=session,
            )
        assert exc_info.value.status_code == 404

    asyncio.run(run())
    statement = session.statements[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "user_sessions.id" in sql
    assert "user_sessions.user_id" in sql
    assert session_id.hex in sql
    assert other_user_id.hex in sql
    assert owner_id.hex not in sql
    assert not session.committed


def test_revoke_all_sessions_is_scoped_to_one_account_and_active_sessions():
    actor_id, target_id = uuid4(), uuid4()
    target_user = SimpleNamespace(id=target_id)
    session = _Session([_Result(target_user), _Result(rowcount=3)])

    result = asyncio.run(
        admin_users.revoke_all_admin_user_sessions(
            user_id=target_id,
            current_user=SimpleNamespace(id=actor_id),
            credentials=None,
            session=session,
        )
    )

    assert result == {"revoked_count": 3}
    mutation = session.statements[1]
    assert isinstance(mutation, type(update(UserSession)))
    sql = str(mutation.compile(compile_kwargs={"literal_binds": True}))
    assert "user_sessions.user_id" in sql
    assert target_id.hex in sql
    assert "user_sessions.revoked_at IS NULL" in sql
    assert "user_sessions.expires_at" in sql
    assert session.committed


def test_last_active_admin_guard_serializes_checks_on_admin_role_row():
    target_id = uuid4()
    role = SimpleNamespace(name="admin")
    session = _Session([_Result("ACTIVE"), _Result(role), _Result(2)])

    asyncio.run(admin_users._protect_last_active_admin(session, target_id))

    assert len(session.statements) == 3
    role_lock_query = session.statements[1]
    assert role_lock_query._for_update_arg is not None


def test_sensitive_account_mutations_lock_target_rows_before_changes():
    import inspect

    guarded_handlers = (
        admin_users.transition_admin_user_lifecycle,
        admin_users.delete_admin_user,
        admin_users.update_admin_user_access_policy,
        admin_users.apply_admin_users_bulk_lifecycle,
    )
    for handler in guarded_handlers:
        assert ".with_for_update()" in inspect.getsource(handler), handler.__name__
