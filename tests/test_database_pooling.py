from sqlalchemy.pool import NullPool

from database.session import _engine_pool_options


def test_vercel_uses_null_pool_for_async_database_connections(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    assert _engine_pool_options() == {"poolclass": NullPool}


def test_non_vercel_environment_keeps_default_database_pool(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert _engine_pool_options() == {}
