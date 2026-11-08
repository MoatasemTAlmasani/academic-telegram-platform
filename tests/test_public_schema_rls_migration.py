"""PostgreSQL DDL contract tests for the public-schema security migration."""

from __future__ import annotations

import importlib.util
from io import StringIO
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.dialects import postgresql


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "migrations"
    / "versions"
    / "bb88cc99dd00_lock_down_public_api_roles.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        MIGRATION_PATH.stem, MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_schema_security_migration_renders_postgresql_hardening_ddl() -> None:
    migration = _load_migration()
    output = StringIO()
    context = MigrationContext.configure(
        dialect=postgresql.dialect(),
        opts={"as_sql": True, "output_buffer": output},
    )

    with Operations.context(context):
        migration.upgrade()

    sql = output.getvalue().lower()
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "create policy" in sql
    assert "current_user not in (''anon'', ''authenticated'')" in sql
    assert "namespace.nspname = 'public'" in sql
    assert "relation.relkind in ('r', 'p')" in sql
    assert "revoke all privileges on all tables in schema public" in sql
    assert "revoke all privileges on all sequences in schema public" in sql
    assert "revoke all privileges on all functions in schema public" in sql
    assert "alter default privileges for role postgres in schema public" in sql
    assert "from anon, authenticated" in sql


def test_public_schema_security_migration_documents_supabase_managed_owner_limit() -> None:
    source = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "not a member of supabase_admin" in source
    assert "create objects as postgres" in source


def test_public_schema_security_migration_follows_current_head() -> None:
    migration = _load_migration()
    assert migration.revision == "bb88cc99dd00"
    assert migration.down_revision == "aa77bb88cc99"


def test_public_schema_security_migration_refuses_unsafe_downgrade() -> None:
    migration = _load_migration()
    with pytest.raises(RuntimeError, match="intentionally irreversible"):
        migration.downgrade()
