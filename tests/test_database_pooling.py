from sqlalchemy.pool import NullPool

from database.session import _engine_pool_options


def test_vercel_uses_null_pool_without_queue_pool_options(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    options = _engine_pool_options()

    assert options == {"poolclass": NullPool}
    assert "pool_size" not in options
    assert "max_overflow" not in options


def test_non_vercel_environment_keeps_bounded_queue_pool(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert _engine_pool_options() == {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_recycle": 1800,
    }
