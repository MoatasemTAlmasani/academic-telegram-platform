from __future__ import annotations

import ast
from pathlib import Path

from backend.app.modules.authentication.permissions import Permission
from backend.app.modules.authentication.roles import (
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
    RoleName,
    permissions_for_role,
)


def test_all_six_roadmap_roles_have_descriptions_and_permission_sets() -> None:
    expected = {
        "super_admin", "admin", "manager", "staff", "support", "customer"
    }
    assert {role.value for role in RoleName} == expected
    assert set(ROLE_DESCRIPTIONS) == set(RoleName)
    assert set(ROLE_PERMISSIONS) == set(RoleName)
    assert all(ROLE_DESCRIPTIONS[role] for role in RoleName)
    assert all(ROLE_PERMISSIONS[role] for role in RoleName)


def test_role_permissions_follow_least_privilege_boundaries() -> None:
    assert permissions_for_role(RoleName.SUPER_ADMIN) == set(Permission)
    assert Permission.ROLES_MANAGE in permissions_for_role(RoleName.SUPER_ADMIN)
    assert Permission.ROLES_MANAGE not in permissions_for_role(RoleName.ADMIN)
    assert Permission.ADMIN_ACCESS in permissions_for_role(RoleName.MANAGER)
    assert Permission.ADMIN_ACCESS in permissions_for_role(RoleName.STAFF)
    assert Permission.ADMIN_ACCESS in permissions_for_role(RoleName.SUPPORT)
    assert Permission.ADMIN_ACCESS not in permissions_for_role(RoleName.CUSTOMER)
    assert Permission.REQUESTS_CREATE in permissions_for_role(RoleName.CUSTOMER)
    assert Permission.USERS_DELETE not in permissions_for_role(RoleName.CUSTOMER)
    assert permissions_for_role("unknown-role") == set()


def test_role_permission_sets_are_returned_as_independent_copies() -> None:
    permissions = permissions_for_role(RoleName.SUPPORT)
    permissions.clear()
    assert Permission.REQUESTS_READ in ROLE_PERMISSIONS[RoleName.SUPPORT]


def test_role_seed_migration_contains_all_six_roles_and_is_chained() -> None:
    migration_path = Path("database/migrations/versions/aa77bb88cc99_seed_six_rbac_roles.py")
    source = migration_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"ROLE_DESCRIPTIONS", "ROLE_PERMISSION_CODES"}
    }
    expected = {role.value for role in RoleName}
    assert set(assignments["ROLE_DESCRIPTIONS"]) == expected
    assert set(assignments["ROLE_PERMISSION_CODES"]) == expected
    migration_matrix = {
        RoleName(name): set(codes)
        for name, codes in assignments["ROLE_PERMISSION_CODES"].items()
    }
    runtime_matrix = {
        role: {permission.value for permission in permissions}
        for role, permissions in ROLE_PERMISSIONS.items()
    }
    assert migration_matrix == runtime_matrix
    assert 'revision = "aa77bb88cc99"' in source
    assert 'down_revision = "ff66aa77bb88"' in source
    assert '"roles:manage"' in source


def test_role_permission_updates_require_the_dedicated_governance_permission() -> None:
    route_source = Path("backend/app/api/routes/rbac_admin.py").read_text(encoding="utf-8")
    assert 'dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))]' in route_source


def test_role_seed_migration_upgrade_and_downgrade_preserve_legacy_role_links() -> None:
    import importlib.util
    import uuid

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import (
        Column,
        ForeignKey,
        MetaData,
        String,
        Table,
        Text,
        Uuid,
        create_engine,
        select,
    )

    migration_path = Path(
        "database/migrations/versions/aa77bb88cc99_seed_six_rbac_roles.py"
    )
    spec = importlib.util.spec_from_file_location("seed_six_roles", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    roles = Table(
        "roles",
        metadata,
        Column("id", Uuid(), primary_key=True),
        Column("name", String(100), nullable=False, unique=True),
        Column("description", Text()),
    )
    permissions = Table(
        "permissions",
        metadata,
        Column("id", Uuid(), primary_key=True),
        Column("code", String(150), nullable=False, unique=True),
        Column("description", Text()),
    )
    role_permissions = Table(
        "role_permissions",
        metadata,
        Column("role_id", Uuid(), ForeignKey("roles.id"), primary_key=True),
        Column("permission_id", Uuid(), ForeignKey("permissions.id"), primary_key=True),
    )
    metadata.create_all(engine)

    legacy_role_id = uuid.uuid4()
    legacy_permission_id = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(
            roles.insert(),
            [
                {"id": legacy_role_id, "name": "admin", "description": "Legacy admin"},
                {"id": uuid.uuid4(), "name": "staff", "description": "Legacy staff"},
                {"id": uuid.uuid4(), "name": "customer", "description": "Legacy customer"},
            ],
        )
        connection.execute(
            permissions.insert().values(
                id=legacy_permission_id,
                code="legacy:permission",
                description="Existing permission",
            )
        )
        connection.execute(
            role_permissions.insert().values(
                role_id=legacy_role_id,
                permission_id=legacy_permission_id,
            )
        )

        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert legacy_permission_id in connection.execute(
            select(role_permissions.c.permission_id).where(
                role_permissions.c.role_id == legacy_role_id
            )
        ).scalars().all()

        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(
            select(roles.c.name).where(roles.c.id == legacy_role_id)
        ).scalar_one() == "admin"
        assert connection.execute(
            select(role_permissions.c.permission_id).where(
                role_permissions.c.role_id == legacy_role_id
            )
        ).scalar_one() == legacy_permission_id
        remaining_roles = set(connection.execute(select(roles.c.name)).scalars())
        assert remaining_roles == {"admin", "staff", "customer"}

    engine.dispose()
