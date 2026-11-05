"""Smoke tests for the refreshed administration entry points and protection."""

import asyncio
import httpx

from backend.app.main import app
from backend.app.api.routes.admin_dashboard import has_dashboard_permission
from backend.app.modules.authentication.permissions import Permission


async def get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_admin_console_entrypoint_is_served() -> None:
    response = asyncio.run(get("/admin"))
    assert response.status_code == 200
    assert "EHTERAF" in response.text
    assert "console.js" in response.text
    assert "dashboard-period-analytics.js" in response.text
    assert "loginForm" in response.text


def test_legacy_admin_console_remains_available() -> None:
    response = asyncio.run(get("/admin/legacy"))
    assert response.status_code == 200
    assert "loginForm" in response.text


def test_admin_access_summary_requires_authentication() -> None:
    response = asyncio.run(get("/api/v1/admin/dashboard/access"))
    assert response.status_code == 401


def test_dashboard_reporting_period_openapi_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/admin/dashboard/overview"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "period_days")
    assert parameter["schema"]["minimum"] == 7
    assert parameter["schema"]["maximum"] == 365
    assert parameter["schema"]["default"] == 30
    assert any(item["name"] == "service_id" for item in operation["parameters"])


def test_dashboard_overview_still_requires_authentication_with_valid_period() -> None:
    response = asyncio.run(get("/api/v1/admin/dashboard/overview?period_days=90"))
    assert response.status_code == 401


def test_dashboard_period_analytics_asset_is_served() -> None:
    response = asyncio.run(get("/admin/static/dashboard-period-analytics.js"))
    assert response.status_code == 200
    assert "refreshDashboardPeriodAnalytics" in response.text
    assert "periodServiceChart" in response.text



def test_dashboard_detail_permissions_are_granular() -> None:
    permissions = {
        Permission.ADMIN_ACCESS.value,
        Permission.REQUESTS_READ.value,
    }

    assert has_dashboard_permission(permissions, Permission.REQUESTS_READ)
    assert not has_dashboard_permission(permissions, Permission.QUOTES_READ)
    assert not has_dashboard_permission(permissions, Permission.AUDIT_READ)
    assert not has_dashboard_permission(permissions, Permission.SERVICES_READ)
