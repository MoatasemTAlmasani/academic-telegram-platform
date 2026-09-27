"""Health endpoint tests."""

import asyncio

import httpx

from backend.app.main import app
from backend.app.core.config import get_settings


async def get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        return await client.get(path)


def test_health_check() -> None:
    response = asyncio.run(get("/health"))

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "ok",
        "service": "academic-services-platform-api",
        "environment": "development",
    }


def test_versioned_health_check() -> None:
    response = asyncio.run(get("/api/v1/health"))

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_readiness_check_reports_unconfigured_dependencies(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    get_settings.cache_clear()

    try:
        response = asyncio.run(get("/health/ready"))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "ready",
        "dependencies": {
            "database": "not_configured",
            "redis": "not_configured",
        },
    }