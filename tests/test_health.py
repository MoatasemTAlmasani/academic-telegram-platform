"""Health endpoint tests."""

import asyncio

import httpx

from backend.app.main import app
from backend.app.api.routes import health


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


class FakeConnection:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def execute(self, _statement):
        return 1


class FakeEngine:
    def connect(self):
        return FakeConnection()


class FailingEngine:
    def connect(self):
        raise OSError("database unavailable")


class FakeSettings:
    database_url = "postgresql://redacted"
    redis_url = None


def test_readiness_check_requires_a_database_probe() -> None:
    from starlette.responses import Response

    response = Response()
    result = asyncio.run(
        health._readiness_response(FakeSettings(), FakeEngine(), response)
    )

    assert response.status_code == 200
    assert result.success is True
    assert result.status == "ready"
    assert result.dependencies == {
        "database": "available",
        "redis": "not_configured",
    }


def test_readiness_check_returns_503_when_database_probe_fails() -> None:
    from starlette.responses import Response

    response = Response()
    result = asyncio.run(
        health._readiness_response(FakeSettings(), FailingEngine(), response)
    )

    assert response.status_code == 503
    assert result.success is False
    assert result.status == "degraded"
    assert result.dependencies["database"] == "unavailable"