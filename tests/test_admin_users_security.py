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
    def __init__(self, value=None, *, rowcount=0, items=None):
        self.value = value
        self.rowcount = rowcount
        self.items = items

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return self.items if self.items is not None else []


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


def test_admin_user_routes_enforce_the_exact_least_privilege_permission_matrix():
    expected = {
        ("GET", "/admin/users"): {Permission.USERS_READ},
        ("GET", "/admin/users/export.csv"): {Permission.USERS_READ},
        ("GET", "/admin/users/{user_id}"): {Permission.USERS_READ},
        ("POST", "/admin/users"): {Permission.USERS_CREATE},
        ("PATCH", "/admin/users/{user_id}"): {Permission.USERS_UPDATE},
        ("POST", "/admin/users/{user_id}/lifecycle"): {Permission.USERS_UPDATE},
        ("DELETE", "/admin/users/{user_id}"): {Permission.USERS_DELETE},
        ("PUT", "/admin/users/{user_id}/role"): {Permission.ROLES_MANAGE},
        ("GET", "/admin/users/{user_id}/access-summary"): {Permission.USERS_READ},
        ("GET", "/admin/users/{user_id}/audit-history"): {Permission.AUDIT_READ},
        ("GET", "/admin/users/{user_id}/login-attempts"): {Permission.USERS_READ},
        ("GET", "/admin/users/{user_id}/activity"): {Permission.USERS_READ, Permission.AUDIT_READ},
        ("GET", "/admin/users/{user_id}/activity.csv"): {Permission.USERS_READ, Permission.AUDIT_READ},
        ("POST", "/admin/users/{user_id}/password-recovery"): {Permission.USERS_UPDATE},
        ("GET", "/admin/users/{user_id}/identities"): {Permission.USERS_READ},
        ("PATCH", "/admin/users/{user_id}/access-policy"): {Permission.USERS_UPDATE},
        ("POST", "/admin/users/bulk/preview"): {Permission.USERS_UPDATE},
        ("POST", "/admin/users/bulk/lifecycle"): {Permission.USERS_UPDATE},
        ("GET", "/admin/users/{user_id}/sessions"): {Permission.USERS_READ},
        ("DELETE", "/admin/users/{user_id}/sessions/{session_id}"): {Permission.USERS_UPDATE},
        ("POST", "/admin/users/{user_id}/sessions/revoke-all"): {Permission.USERS_UPDATE},
    }

    routes = [route for route in admin_users.router.routes if isinstance(route, APIRoute)]
    actual = {}
    for route in routes:
        assert len(route.methods) == 1, f"Unexpected methods for {route.path}: {route.methods}"
        method = next(iter(route.methods))
        dependencies = list(_dependency_tree(route.dependant.dependencies))
        granted = set()
        for dependency in dependencies:
            call = dependency.call
            if call is None or getattr(call, "__name__", None) != "permission_dependency":
                continue
            for cell in call.__closure__ or ():
                value = cell.cell_contents
                if isinstance(value, Permission):
                    granted.add(value)
        actual[(method, route.path)] = granted

    assert actual == expected, (
        f"Module 02 route permission matrix changed. "
        f"Missing={expected.keys() - actual.keys()}, "
        f"unexpected={actual.keys() - expected.keys()}, "
        f"changed={ {key: (expected[key], actual[key]) for key in expected.keys() & actual.keys() if expected[key] != actual[key]} }"
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

    assert len(session.statements) == 4
    role_lock_query = session.statements[1]
    assert role_lock_query._for_update_arg is not None
    assert "super_admin" in session.statements[3].compile().params.values()


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


def test_custom_role_assignment_is_supported_and_revokes_existing_sessions():
    actor_id, target_id, role_id = uuid4(), uuid4(), uuid4()
    previous_role = SimpleNamespace(name="staff")
    target = SimpleNamespace(
        id=target_id,
        username="target-user",
        status="ACTIVE",
        roles=[previous_role],
    )
    custom_role = SimpleNamespace(
        id=role_id,
        name="regional_manager",
        description="Regional operations",
        permissions=[],
    )
    session = _Session([
        _Result(target),
        _Result(custom_role),
        _Result(rowcount=2),
    ])

    payload = admin_users.AdminUserRoleAssignmentRequest(
        role="  REGIONAL_MANAGER  "
    )
    response = asyncio.run(
        admin_users.assign_admin_user_role(
            user_id=target_id,
            payload=payload,
            current_user=SimpleNamespace(
                id=actor_id,
                roles=[
                    SimpleNamespace(
                        name="super_admin",
                        permissions=[
                            SimpleNamespace(code="roles:manage"),
                            SimpleNamespace(code="users:read"),
                        ],
                    )
                ],
            ),
            session=session,
        )
    )

    assert response.role.name == "regional_manager"
    assert response.sessions_revoked == 2
    assert target.roles == [custom_role]
    assert session.committed
    assert session.added[0].action == "user.role_assigned"
    assert session.added[0].event_metadata["before_roles"] == ["staff"]
    assert session.added[0].event_metadata["after_roles"] == ["regional_manager"]


def test_custom_role_assignment_cannot_demote_the_last_active_super_admin():
    actor_id, target_id = uuid4(), uuid4()
    target = SimpleNamespace(
        id=target_id,
        username="last-super-admin",
        status="ACTIVE",
        roles=[SimpleNamespace(name="super_admin")],
    )
    replacement_role = SimpleNamespace(
        id=uuid4(),
        name="regional_manager",
        description="Regional operations",
        permissions=[],
    )
    super_admin_role = SimpleNamespace(name="super_admin")
    session = _Session([
        _Result(target),
        _Result(replacement_role),
        _Result("ACTIVE"),
        _Result(super_admin_role),
        _Result(1),
    ])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await admin_users.assign_admin_user_role(
                user_id=target_id,
                payload=admin_users.AdminUserRoleAssignmentRequest(
                    role="regional_manager"
                ),
                current_user=SimpleNamespace(id=actor_id),
                session=session,
            )
        assert exc_info.value.status_code == 409
        assert "last active Super Admin" in exc_info.value.detail

    asyncio.run(scenario())
    assert len(session.statements) == 5
    assert session.statements[3]._for_update_arg is not None
    assert not session.committed
    assert not session.added
    assert [role.name for role in target.roles] == ["super_admin"]


def test_role_assignment_cannot_grant_super_admin_to_non_super_admin_actor():
    actor_id, target_id = uuid4(), uuid4()
    target = SimpleNamespace(
        id=target_id,
        username="target-user",
        status="ACTIVE",
        roles=[],
    )
    super_admin_role = SimpleNamespace(
        id=uuid4(),
        name="super_admin",
        description="Protected role",
        permissions=[],
    )
    session = _Session([_Result(target), _Result(super_admin_role)])
    actor = SimpleNamespace(
        id=actor_id,
        roles=[
            SimpleNamespace(
                name="admin",
                permissions=[SimpleNamespace(code="roles:manage")],
            )
        ],
    )

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await admin_users.assign_admin_user_role(
                user_id=target_id,
                payload=admin_users.AdminUserRoleAssignmentRequest(role="super_admin"),
                current_user=actor,
                session=session,
            )
        assert exc_info.value.status_code == 403

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_role_assignment_cannot_exceed_the_actors_effective_permissions():
    actor_id, target_id = uuid4(), uuid4()
    target = SimpleNamespace(
        id=target_id,
        username="target-user",
        status="ACTIVE",
        roles=[],
    )
    custom_role = SimpleNamespace(
        id=uuid4(),
        name="regional_manager",
        description="Regional manager",
        permissions=[SimpleNamespace(code="users:delete")],
    )
    actor = SimpleNamespace(
        id=actor_id,
        roles=[
            SimpleNamespace(
                name="admin",
                permissions=[
                    SimpleNamespace(code="roles:manage"),
                    SimpleNamespace(code="users:read"),
                ],
            )
        ],
    )
    session = _Session([_Result(target), _Result(custom_role)])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await admin_users.assign_admin_user_role(
                user_id=target_id,
                payload=admin_users.AdminUserRoleAssignmentRequest(
                    role="regional_manager"
                ),
                current_user=actor,
                session=session,
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["unauthorized_permissions"] == ["users:delete"]

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_multi_role_assignment_unions_permissions_and_revokes_sessions():
    actor_id, target_id = uuid4(), uuid4()
    target = SimpleNamespace(
        id=target_id,
        username="multi-role-target",
        status="ACTIVE",
        roles=[SimpleNamespace(name="staff")],
    )
    manager = SimpleNamespace(
        id=uuid4(),
        name="manager",
        description="Manager",
        permissions=[SimpleNamespace(code="requests:read")],
    )
    support = SimpleNamespace(
        id=uuid4(),
        name="support",
        description="Support",
        permissions=[SimpleNamespace(code="users:read")],
    )
    actor = SimpleNamespace(
        id=actor_id,
        roles=[
            SimpleNamespace(
                name="super_admin",
                permissions=[
                    SimpleNamespace(code="roles:manage"),
                    SimpleNamespace(code="requests:read"),
                    SimpleNamespace(code="users:read"),
                ],
            )
        ],
    )
    session = _Session([
        _Result(target),
        _Result(items=[manager, support]),
        _Result(rowcount=3),
    ])

    response = asyncio.run(
        admin_users.assign_admin_user_roles(
            user_id=target_id,
            payload=admin_users.AdminUserRolesAssignmentRequest(
                role_names=[" SUPPORT ", "manager"]
            ),
            current_user=actor,
            session=session,
        )
    )

    assert [role.name for role in response.roles] == ["manager", "support"]
    assert response.sessions_revoked == 3
    assert [role.name for role in target.roles] == ["manager", "support"]
    assert session.committed
    assert session.added[0].action == "user.roles_assigned"
    assert session.added[0].event_metadata["before_roles"] == ["staff"]
    assert session.added[0].event_metadata["after_roles"] == ["manager", "support"]


def test_multi_role_assignment_rejects_permissions_beyond_grantor_access():
    actor_id, target_id = uuid4(), uuid4()
    target = SimpleNamespace(
        id=target_id,
        username="restricted-target",
        status="ACTIVE",
        roles=[],
    )
    restricted_role = SimpleNamespace(
        id=uuid4(),
        name="regional_manager",
        description="Regional manager",
        permissions=[SimpleNamespace(code="users:delete")],
    )
    actor = SimpleNamespace(
        id=actor_id,
        roles=[
            SimpleNamespace(
                name="admin",
                permissions=[SimpleNamespace(code="roles:manage"), SimpleNamespace(code="users:read")],
            )
        ],
    )
    session = _Session([
        _Result(target),
        _Result(items=[restricted_role]),
    ])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await admin_users.assign_admin_user_roles(
                user_id=target_id,
                payload=admin_users.AdminUserRolesAssignmentRequest(
                    role_names=["regional_manager"]
                ),
                current_user=actor,
                session=session,
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["unauthorized_permissions"] == ["users:delete"]

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_user_access_panel_uses_permission_gated_multi_role_assignment_ui():
    from pathlib import Path

    html = Path("backend/app/static/admin/console.html").read_text(encoding="utf-8")
    script = Path("backend/app/static/admin/console.js").read_text(encoding="utf-8")
    assert 'id="userRoleChoices"' in html
    assert 'id="userAccessState"' in html
    assert 'data-user-role-choice' in script
    assert 'data.access_enabled' in script
    assert '"/roles",{method:"PUT"' in script
    assert 'form.hidden=!has("roles:manage")' in script
