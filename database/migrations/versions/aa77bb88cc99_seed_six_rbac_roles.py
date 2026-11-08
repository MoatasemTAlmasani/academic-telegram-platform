"""Seed the six roadmap roles and their least-privilege permissions.

Revision ID: aa77bb88cc99
Revises: ff66aa77bb88
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa

revision = "aa77bb88cc99"
down_revision = "ff66aa77bb88"
branch_labels = None
depends_on = None

ROLE_DESCRIPTIONS = {
    "super_admin": "Full platform control, including role and permission governance.",
    "admin": "Platform administration and operational management, excluding role governance.",
    "manager": "Supervises staff and operational workflows across requests and services.",
    "staff": "Performs assigned service, request, file, and quotation work.",
    "support": "Handles customer support and request follow-up with limited access.",
    "customer": "Submits and follows up on personal service requests.",
}

# Keep this migration self-contained; changing runtime policy must not rewrite history.
ROLE_PERMISSION_CODES = {
    "super_admin": {
        "users:read", "users:create", "users:update", "users:delete",
        "services:read", "services:create", "services:update", "services:delete",
        "requests:read", "requests:create", "requests:update",
        "files:read", "files:upload", "files:delete",
        "quotes:read", "quotes:create", "quotes:update",
        "content:read", "content:create", "content:update", "content:delete",
        "campaigns:read", "campaigns:create", "campaigns:update", "campaigns:delete",
        "telegram:read", "telegram:manage", "audit:read", "admin:access", "roles:manage",
    },
    "admin": {
        "users:read", "users:create", "users:update", "users:delete",
        "services:read", "services:create", "services:update", "services:delete",
        "requests:read", "requests:create", "requests:update",
        "files:read", "files:upload", "files:delete",
        "quotes:read", "quotes:create", "quotes:update",
        "content:read", "content:create", "content:update", "content:delete",
        "campaigns:read", "campaigns:create", "campaigns:update", "campaigns:delete",
        "telegram:read", "telegram:manage", "audit:read", "admin:access",
    },
    "manager": {
        "admin:access", "users:read", "services:read", "services:update",
        "requests:read", "requests:update", "files:read", "files:upload",
        "quotes:read", "quotes:create", "quotes:update",
        "content:read", "content:create", "content:update",
        "campaigns:read", "campaigns:create", "campaigns:update",
        "telegram:read", "audit:read",
    },
    "staff": {
        "admin:access", "users:read", "services:read", "services:update",
        "requests:read", "requests:update", "files:read", "files:upload",
        "quotes:read", "quotes:create", "quotes:update",
        "content:read", "content:create", "content:update", "telegram:read",
    },
    "support": {
        "admin:access", "users:read", "services:read", "requests:read",
        "requests:update", "files:read", "files:upload", "quotes:read", "telegram:read",
    },
    "customer": {
        "services:read", "requests:read", "requests:create", "files:read",
        "files:upload", "quotes:read", "content:read", "telegram:read",
    },
}

PERMISSION_DESCRIPTIONS = {
    code: code.replace(":", " ").replace("_", " ").capitalize()
    for codes in ROLE_PERMISSION_CODES.values()
    for code in codes
}


def upgrade() -> None:
    bind = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(100)),
        sa.column("description", sa.Text()),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(150)),
        sa.column("description", sa.Text()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    role_backup = op.create_table(
        "rbac_roles_backup_aa77bb88cc99",
        sa.Column("role_id", sa.Uuid(), primary_key=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    role_permission_backup = op.create_table(
        "rbac_role_permissions_backup_aa77bb88cc99",
        sa.Column("role_id", sa.Uuid(), primary_key=True),
        sa.Column("permission_id", sa.Uuid(), primary_key=True),
    )

    role_ids: dict[str, uuid.UUID] = {}
    for name, description in ROLE_DESCRIPTIONS.items():
        existing_row = bind.execute(
            sa.select(roles.c.id, roles.c.description).where(roles.c.name == name)
        ).first()
        existing = existing_row.id if existing_row else None
        role_id = existing or uuid.uuid4()
        if existing_row is not None:
            bind.execute(
                role_backup.insert().values(
                    role_id=existing_row.id,
                    description=existing_row.description,
                )
            )
            prior_links = bind.execute(
                sa.select(role_permissions.c.role_id, role_permissions.c.permission_id).where(
                    role_permissions.c.role_id == existing_row.id
                )
            ).all()
            if prior_links:
                bind.execute(
                    role_permission_backup.insert(),
                    [
                        {"role_id": row.role_id, "permission_id": row.permission_id}
                        for row in prior_links
                    ],
                )
        if existing is None:
            bind.execute(roles.insert().values(id=role_id, name=name, description=description))
        else:
            bind.execute(roles.update().where(roles.c.id == role_id).values(description=description))
        role_ids[name] = role_id

    permission_ids: dict[str, uuid.UUID] = {}
    all_codes = sorted(PERMISSION_DESCRIPTIONS)
    for code in all_codes:
        existing = bind.execute(
            sa.select(permissions.c.id).where(permissions.c.code == code)
        ).scalar_one_or_none()
        permission_id = existing or uuid.uuid4()
        if existing is None:
            bind.execute(
                permissions.insert().values(
                    id=permission_id,
                    code=code,
                    description=PERMISSION_DESCRIPTIONS[code],
                )
            )
        permission_ids[code] = permission_id

    for role_name, codes in ROLE_PERMISSION_CODES.items():
        for code in sorted(codes):
            exists = bind.execute(
                sa.select(role_permissions.c.role_id).where(
                    role_permissions.c.role_id == role_ids[role_name],
                    role_permissions.c.permission_id == permission_ids[code],
                )
            ).first()
            if exists is None:
                bind.execute(
                    role_permissions.insert().values(
                        role_id=role_ids[role_name],
                        permission_id=permission_ids[code],
                    )
                )


def downgrade() -> None:
    bind = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(100)),
        sa.column("description", sa.Text()),
    )
    permissions = sa.table(
        "permissions", sa.column("id", sa.Uuid()), sa.column("code", sa.String(150))
    )
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", sa.Uuid()), sa.column("permission_id", sa.Uuid())
    )

    role_rows = bind.execute(
        sa.select(roles.c.id, roles.c.name).where(roles.c.name.in_(ROLE_DESCRIPTIONS))
    ).all()
    role_ids = [row.id for row in role_rows]
    if role_ids:
        bind.execute(role_permissions.delete().where(role_permissions.c.role_id.in_(role_ids)))

        # Restore the exact permission assignments that existed before this revision.
        backup_links = sa.table(
            "rbac_role_permissions_backup_aa77bb88cc99",
            sa.column("role_id", sa.Uuid()),
            sa.column("permission_id", sa.Uuid()),
        )
        prior_links = bind.execute(
            sa.select(backup_links.c.role_id, backup_links.c.permission_id)
        ).all()
        if prior_links:
            bind.execute(
                role_permissions.insert(),
                [
                    {"role_id": row.role_id, "permission_id": row.permission_id}
                    for row in prior_links
                ],
            )

        # Remove only the three roles introduced by this revision.
        new_role_ids = [
            row.id for row in role_rows
            if row.name in {"super_admin", "manager", "support"}
        ]
        if new_role_ids:
            bind.execute(roles.delete().where(roles.c.id.in_(new_role_ids)))

    role_backup = sa.table(
        "rbac_roles_backup_aa77bb88cc99",
        sa.column("role_id", sa.Uuid()),
        sa.column("description", sa.Text()),
    )
    prior_roles = bind.execute(
        sa.select(role_backup.c.role_id, role_backup.c.description)
    ).all()
    for row in prior_roles:
        bind.execute(
            roles.update().where(roles.c.id == row.role_id).values(description=row.description)
        )
    op.drop_table("rbac_role_permissions_backup_aa77bb88cc99")
    op.drop_table("rbac_roles_backup_aa77bb88cc99")

    roles_manage_id = bind.execute(
        sa.select(permissions.c.id).where(permissions.c.code == "roles:manage")
    ).scalar_one_or_none()
    if roles_manage_id is not None:
        remaining = bind.execute(
            sa.select(role_permissions.c.role_id).where(
                role_permissions.c.permission_id == roles_manage_id
            )
        ).first()
        if remaining is None:
            bind.execute(permissions.delete().where(permissions.c.id == roles_manage_id))
