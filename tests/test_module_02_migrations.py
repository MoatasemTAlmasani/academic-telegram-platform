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
                    migration.upgrade()

            inspector = inspect(connection)
            expected_tables = {
                "user_sessions",
                "login_attempts",
                "external_identities",
                "identity_link_challenges",
            }
            assert expected_tables.issubset(set(inspector.get_table_names()))
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            assert {"locked_until", "account_expires_at", "preferences"}.issubset(user_columns)

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


def test_password_recovery_migration_is_chained_and_reversible() -> None:
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "versions"
        / "ee55ff66aa77_password_recovery_challenges.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "ee55ff66aa77"' in migration
    assert 'down_revision: Union[str, Sequence[str], None] = "dd44ee55ff66"' in migration
    assert 'op.create_table(\n        "password_recovery_attempts"' in migration
    assert 'op.create_table(\n        "password_recovery_challenges"' in migration
    assert 'op.drop_table("password_recovery_challenges")' in migration
    assert 'op.drop_table("password_recovery_attempts")' in migration


def test_password_recovery_migration_upgrade_and_downgrade_on_isolated_sqlite() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    migration_path = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "versions"
        / "ee55ff66aa77_password_recovery_challenges.py"
    )
    spec = spec_from_file_location("password_recovery_migration", migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = sa.create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            users = sa.Table(
                "users",
                sa.MetaData(),
                sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            )
            users.create(connection)
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()

            inspector = sa.inspect(connection)
            assert "password_recovery_attempts" in inspector.get_table_names()
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


def test_user_last_seen_timezone_migration_is_chained_and_reversible() -> None:
    migration = (MIGRATIONS / "ff66aa77bb88_user_last_seen_timezone.py").read_text(
        encoding="utf-8"
    )
    model = (Path(__file__).resolve().parents[1] / "database" / "models" / "identity.py").read_text(
        encoding="utf-8"
    )

    assert 'revision: str = "ff66aa77bb88"' in migration
    assert 'down_revision: Union[str, Sequence[str], None] = "ee55ff66aa77"' in migration
    assert 'type_=sa.DateTime(timezone=True)' in migration
    assert 'postgresql_using="last_seen_at AT TIME ZONE \'UTC\'"' in migration
    assert 'type_=sa.DateTime()' in migration
    assert 'DateTime(timezone=True), nullable=True' in model
