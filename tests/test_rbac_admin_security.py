from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.api.routes.rbac_admin import (
    RBACRolePermissionUpdateRequest,
    update_role_permissions,
)


class _Result:
    def __init__(self, value=None, items=None):
        self.value = value
        self.items = items

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.items if self.items is not None else []


class _Session:
    def __init__(self, results):
        self.results = list(results)
        self.statements = []
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.committed = True

    async def refresh(self, item):
        self.refreshed.append(item)


def test_rbac_update_locks_role_row_before_mutation():
    role = SimpleNamespace(id=uuid4(), name="manager", description="Manager role", permissions=[])
    session = _Session([_Result(role), _Result(role)])

    asyncio.run(
        update_role_permissions(
            role_id=role.id,
            payload=RBACRolePermissionUpdateRequest(permission_codes=[]),
            current_user=SimpleNamespace(id=uuid4()),
            session=session,
        )
    )

    assert session.statements[0]._for_update_arg is not None


def test_rbac_update_cannot_modify_super_admin_permissions():
    role = SimpleNamespace(id=uuid4(), name="super_admin", permissions=[])
    session = _Session([_Result(role)])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await update_role_permissions(
                role_id=role.id,
                payload=RBACRolePermissionUpdateRequest(permission_codes=[]),
                current_user=SimpleNamespace(id=uuid4()),
                session=session,
            )
        assert exc_info.value.status_code == 409

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_rbac_update_cannot_delegate_roles_manage_to_another_role():
    role = SimpleNamespace(id=uuid4(), name="admin", permissions=[])
    session = _Session([_Result(role)])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await update_role_permissions(
                role_id=role.id,
                payload=RBACRolePermissionUpdateRequest(
                    permission_codes=["roles:manage"]
                ),
                current_user=SimpleNamespace(id=uuid4()),
                session=session,
            )
        assert exc_info.value.status_code == 422

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_rbac_permission_change_is_audited_with_before_and_after_codes():
    old_permission = SimpleNamespace(id=uuid4(), code="users:read", description="Read users")
    new_permission = SimpleNamespace(id=uuid4(), code="requests:read", description="Read requests")
    role = SimpleNamespace(
        id=uuid4(),
        name="manager",
        description="Manager role",
        permissions=[old_permission],
    )
    actor = SimpleNamespace(id=uuid4())
    session = _Session([
        _Result(role),
        _Result(items=[new_permission]),
        _Result(role),
    ])

    response = asyncio.run(
        update_role_permissions(
            role_id=role.id,
            payload=RBACRolePermissionUpdateRequest(
                permission_codes=["requests:read"]
            ),
            current_user=actor,
            session=session,
        )
    )

    assert session.committed
    assert role.permissions == [new_permission]
    assert response.role.name == "manager"
    assert [item.code for item in response.role.permissions] == ["requests:read"]
    assert len(session.added) == 1

    audit = session.added[0]
    assert audit.actor_id == actor.id
    assert audit.action == "rbac.role_permissions_updated"
    assert audit.resource_type == "role"
    assert audit.resource_id == role.id
    assert audit.event_metadata == {
        "role_name": "manager",
        "before": ["users:read"],
        "after": ["requests:read"],
    }


def test_rbac_noop_permission_update_does_not_create_audit_event():
    permission = SimpleNamespace(id=uuid4(), code="users:read", description="Read users")
    role = SimpleNamespace(
        id=uuid4(),
        name="manager",
        description="Manager role",
        permissions=[permission],
    )
    session = _Session([
        _Result(role),
        _Result(items=[permission]),
        _Result(role),
    ])

    asyncio.run(
        update_role_permissions(
            role_id=role.id,
            payload=RBACRolePermissionUpdateRequest(
                permission_codes=["users:read"]
            ),
            current_user=SimpleNamespace(id=uuid4()),
            session=session,
        )
    )

    assert not session.committed
    assert not session.added


def test_rbac_ui_disables_permission_edits_without_governance_authority():
    from pathlib import Path

    source = Path("backend/app/static/admin/console.js").read_text(encoding="utf-8")
    assert 'var canEdit=has("roles:manage")&&r.name!=="super_admin";' in source
    assert 'var disabledAttr=canEdit?"":" disabled";' in source
    assert '(canEdit?\'\':\' hidden disabled\')' in source
    assert "The Super Admin permission set is protected." in source


def test_custom_role_creation_normalizes_input_and_writes_audit_event():
    from backend.app.api.routes.rbac_admin import (
        RBACRoleCreateRequest,
        create_custom_role,
    )
    from database.models.identity import Role

    class CreationSession(_Session):
        async def flush(self):
            for item in self.added:
                if isinstance(item, Role) and item.id is None:
                    item.id = uuid4()

    actor = SimpleNamespace(id=uuid4())
    session = CreationSession([_Result(None)])
    payload = RBACRoleCreateRequest(
        name="  regional_manager  ",
        description="  Regional operations  ",
    )

    response = asyncio.run(
        create_custom_role(payload=payload, current_user=actor, session=session)
    )

    assert response.role.name == "regional_manager"
    assert response.role.description == "Regional operations"
    assert response.role.permissions == []
    assert session.committed
    assert len(session.added) == 2
    audit = session.added[1]
    assert audit.actor_id == actor.id
    assert audit.action == "rbac.role_created"
    assert audit.resource_type == "role"
    assert audit.resource_id == response.role.id
    assert audit.event_metadata == {
        "role_name": "regional_manager",
        "description": "Regional operations",
        "role_type": "custom",
    }


def test_custom_role_creation_rejects_canonical_system_role_names():
    from backend.app.api.routes.rbac_admin import (
        RBACRoleCreateRequest,
        create_custom_role,
    )

    session = _Session([])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await create_custom_role(
                payload=RBACRoleCreateRequest(name="admin"),
                current_user=SimpleNamespace(id=uuid4()),
                session=session,
            )
        assert exc_info.value.status_code == 409

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_custom_role_creation_rejects_duplicate_names():
    from backend.app.api.routes.rbac_admin import (
        RBACRoleCreateRequest,
        create_custom_role,
    )

    session = _Session([_Result(SimpleNamespace(name="regional_manager"))])

    async def scenario():
        with pytest.raises(HTTPException) as exc_info:
            await create_custom_role(
                payload=RBACRoleCreateRequest(name="regional_manager"),
                current_user=SimpleNamespace(id=uuid4()),
                session=session,
            )
        assert exc_info.value.status_code == 409

    asyncio.run(scenario())
    assert not session.committed
    assert not session.added


def test_custom_role_creation_ui_is_gated_by_roles_manage_and_uses_existing_api():
    from pathlib import Path

    source = Path("backend/app/static/admin/console.js").read_text(encoding="utf-8")
    assert 'has("roles:manage")?\'<form id="createRoleForm"' in source
    assert 'api("/rbac/roles",{method:"POST"' in source
    assert 'selectedRole=created.role.id' in source
