"""Smoke tests for the refreshed administration entry points and protection."""

import asyncio
import httpx

from backend.app.main import app
from backend.app.api.routes.admin_dashboard import has_dashboard_permission
from backend.app.modules.authentication.permissions import Permission
from backend.app.api.routes.admin_requests import AdminRequestUpdate
from database.models.enums import RequestPriority, ServiceRequestStatus
from pydantic import ValidationError


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
    assert 'id="globalSearch"' in response.text
    assert 'id="auditSearch"' in response.text
    assert 'id="auditPrev"' in response.text
    assert 'id="auditNext"' in response.text
    assert 'id="dashboardQuickActions"' in response.text
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



def test_request_management_exposes_create_read_update_archive_routes() -> None:
    paths = app.openapi()["paths"]
    assert {"get", "post"}.issubset(paths["/api/v1/admin/requests"].keys())
    assert {"get", "patch", "delete"}.issubset(paths["/api/v1/admin/requests/{request_id}"].keys())


def test_staff_management_exposes_full_crud_routes() -> None:
    paths = app.openapi()["paths"]
    assert {"get", "post"}.issubset(paths["/api/v1/admin/staff"].keys())
    assert {"get", "patch", "delete"}.issubset(paths["/api/v1/admin/staff/{user_id}"].keys())


def test_service_management_exposes_full_crud_routes() -> None:
    paths = app.openapi()["paths"]
    assert {"get", "post"}.issubset(paths["/api/v1/admin/services"].keys())
    assert {"get", "patch", "delete"}.issubset(paths["/api/v1/admin/services/{service_id}"].keys())


def test_dashboard_detail_permissions_are_granular() -> None:
    permissions = {
        Permission.ADMIN_ACCESS.value,
        Permission.REQUESTS_READ.value,
    }

    assert has_dashboard_permission(permissions, Permission.REQUESTS_READ)
    assert not has_dashboard_permission(permissions, Permission.QUOTES_READ)
    assert not has_dashboard_permission(permissions, Permission.AUDIT_READ)
    assert not has_dashboard_permission(permissions, Permission.SERVICES_READ)


def test_audit_search_contract_is_exposed_and_authenticated() -> None:
    operation = app.openapi()["paths"]["/api/v1/admin/audit-logs"]["get"]
    assert any(item["name"] == "search" for item in operation["parameters"])

    response = asyncio.run(get("/api/v1/admin/audit-logs?search=login&limit=25&offset=0"))
    assert response.status_code == 401


def test_admin_console_assets_include_search_and_drill_down() -> None:
    response = asyncio.run(get("/admin/static/console.js"))
    assert response.status_code == 200
    assert "bindGlobalSearch" in response.text
    assert 'has("requests:read")' in response.text
    assert "data-metric-page" in response.text

def test_admin_request_update_schema_accepts_only_supported_fields() -> None:
    payload = AdminRequestUpdate(
        status=ServiceRequestStatus.UNDER_REVIEW,
        priority=RequestPriority.HIGH,
        notes="Reviewed by administration",
    )
    assert payload.status is ServiceRequestStatus.UNDER_REVIEW
    assert payload.priority is RequestPriority.HIGH

    try:
        AdminRequestUpdate(status="UNKNOWN", arbitrary_field="not allowed")
    except ValidationError:
        pass
    else:
        raise AssertionError("Unknown request fields and status values must be rejected.")
