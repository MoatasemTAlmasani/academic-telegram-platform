"""Isolated SQLite coverage for Module 02 Alembic revisions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Uuid, create_engine, inspect, text


MIGRATIONS = Path(__file__).resolve().parents[1] / "database" / "migrations" / "versions"


def _load_migration(filename: str):
    path = MIGRATIONS / filename
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_02_migrations_upgrade_and_downgrade_in_isolated_database() -> None:
    engine = create_engine("sqlite:///:memory:")
    migrations = [
        _load_migration("aa11bb22cc33_add_user_sessions.py"),
        _load_migration("bb22cc33dd44_add_login_attempts.py"),
        _load_migration("cc33dd44ee55_external_identity_linking.py"),
        _load_migration("dd44ee55ff66_user_preferences_and_account_controls.py"),
    ]

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE users (id CHAR(32) PRIMARY KEY)"
                )
            )
            with Operations.context(MigrationContext.configure(connection)):
                for migration in migrations:
                    migratiom®éÜj×assword_recovery_attempts" in inspector.get_table_names()
            assert "password_recovery_challenges" in inspector.get_table_names()
            assert {column["name"] for column in inspector.get_columns("password_recovery_challenges")} >= {
                "user_id", "token_hash", "delivery_status", "failed_attempts",
                "expires_at", "delivered_at", "consumed_at",
            }

            with Operations.context(context):
                migration.downgrade()
            inspector = sa.inspect(connection)
            assert "password_recovery_attempts" not in inspector.get_table_names()
            assert "password_recovery_challenges" not in inspector.get_table_names()
    finally:
        engine.dispose()
