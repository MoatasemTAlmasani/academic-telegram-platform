from database.url import normalize_async_database_url


def test_plain_postgres_url_uses_asyncpg_by_default():
    url = normalize_async_database_url(
        "postgresql://app:password@db.example.com:5432/app"
    )

    assert url.startswith("postgresql+asyncpg://")
    assert "password" in url


def test_explicit_psycopg_async_driver_is_preserved():
    url = normalize_async_database_url(
        "postgresql+psycopg://app:password@db.example.com:5432/app"
    )

    assert url.startswith("postgresql+psycopg://")


def test_explicit_asyncpg_driver_is_preserved():
    url = normalize_async_database_url(
        "postgresql+asyncpg://app:password@db.example.com:5432/app"
    )

    assert url.startswith("postgresql+asyncpg://")
