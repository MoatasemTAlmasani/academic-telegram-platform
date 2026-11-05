"""Database URL normalization for the async PostgreSQL engine."""

from sqlalchemy.engine import make_url


def normalize_async_database_url(value: str) -> str:
    """Return an async-driver URL without ever echoing credentials in errors.

    Supabase's PostgreSQL endpoints use asyncpg by default. An explicitly
    configured psycopg async URL remains supported for environments that
    have been validated with that driver.
    """
    try:
        url = make_url(value)
    except Exception as exc:
        raise ValueError("DATABASE_URL is not a valid SQLAlchemy URL.") from exc

    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    if url.drivername not in {
        "postgresql+psycopg",
        "postgresql+asyncpg",
    }:
        raise ValueError(
            "DATABASE_URL must use the PostgreSQL psycopg or asyncpg async driver."
        )

    return url.render_as_string(hide_password=False)
