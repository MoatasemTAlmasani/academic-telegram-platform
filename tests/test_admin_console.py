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
