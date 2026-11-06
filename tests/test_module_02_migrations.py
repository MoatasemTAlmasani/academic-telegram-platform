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
                    migration.upgrade()

            inspector = inspect(connection)
            expected_tables = {
                "user_sessions",
                "login_attempts",
                "external_identities",
                "identity_link_challenges",
            }
            assert expected_tables.issubset(set(inspector.get_table_names()))

            assert {
                index["name"] for index in inspector.get_indexes("user_sessions")
            } >= {
                "ix_user_sessions_user_id",
                "ix_user_sessions_expires_at",
                "ix_user_sessions_revoked_at",
            }
            assert {
                index["name"] for index in inspector.get_indexes("login_attempts")
            } >= {
                "ix_login_attempts_username_time",
                "ix_login_attempts_ip_time",
                "ix_login_attempts_attempted_at",
            }
            assert {
                index["name"] for index in inspector.get_indexes("external_identities")
            } >= {"ix_external_identities_user_id"}

            identity_unique = {
                tuple(item["column_names"])
                for item in inspector.get_unique_constraints("external_identities")
            }
            assert ("provider", "subject") in identity_unique
            assert ("user_id", "provider") in identity_unique

            challenge_unique = {
                tuple(item["column_names"])
                for item in inspector.get_unique_constraints("identity_link_challenges")
            }
            assert ("token_hash",) in challenge_unique

            with Operations.context(MigrationContext.configure(connection)):
                for migration in reversed(migrations):
                    migration.downgrade()

            remaining = set(inspect(connection).get_table_names())
            assert not expected_tables.intersection(remaining)
    finally:
        engine.dispose()
