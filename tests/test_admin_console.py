"""Smoke tests for the refreshed administration entry points and protection."""

import asyncio
import httpx

from backend.app.main import app


async def get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_admin_console_entrypoint_is_served() -> None:
    response = asyncio.run(get("/admin"))
    assert response.status_code == 200
    assert "EHTERAF" in response.text
    assert "console.js" in response.text
    assert "loginForm" in response.text


def test_legacy_admin_console_remains_available() -> None:
    response = asyncio.run(get("/admin/legacy"))
    assert response.status_code == 200
    assert "loginForm" in response.text


def test_admin_access_summary_requires_authentication() -> None:
    response = asyncio.run(get("/api/v1/admin/dashboard/access"))
    assert response.status_code == 401


def test_dashboard_reporting_period_rejects_values_outside_supported_range() -> None:
    too_short = asyncio.run(get("/api/v1/admin/dashboard/overview?period_days=1"))
    too_long = asyncio.run(get("/api/v1/admin/dashboard/overview?period_days=366"))
    assert too_short.status_code == 422
    assert too_long.status_code == 422


def test_dashboard_overview_still_requires_authentication_with_valid_period() -> None:
    response = asyncio.run(get("/api/v1/admin/dashboard/overview?period_days=90"))
    assert response.status_code == 401
