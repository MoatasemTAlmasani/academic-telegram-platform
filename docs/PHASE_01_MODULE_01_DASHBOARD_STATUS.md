# Phase 01 · Module 01 — Dashboard Delivery Status

**Branch:** `feature/admin-system-delivery`  
**Module status:** `IN_PROGRESS`  
**Last updated:** 2026-11-06

This file records implementation evidence and remaining work. It does not mark the dashboard as complete or verified.

## Existing capability retained

- Existing authenticated `/admin` console and `/admin/legacy` route are preserved.
- Existing FastAPI dashboard endpoints, persisted aggregates, customer/request/service/staff/quotation/audit records, bilingual console, RTL/LTR, and light/dark theme remain in place.
- Revenue and receivables remain unavailable because no authoritative invoice/payment ledger exists.
- Staff performance remains unavailable because requests do not yet have staff assignment.
- Branch performance remains unavailable because organization/branch data scopes are not yet implemented.

## Implemented in this delivery slice

| Item | Status | Evidence |
|---|---|---|
| Selectable analytics period (7, 30, 90, 365 days) | IMPLEMENTED | `dashboard-period-analytics.js` |
| Service filter across request-focused dashboard analytics and operations | IMPLEMENTED | `service_id` API filter and `dashboardServiceFilter` control; user/customer totals remain platform-wide |
| Backend period parameter with bounded validation | IMPLEMENTED | `GET /api/v1/admin/dashboard/overview?period_days=` |
| Period-scoped new-customer count | IMPLEMENTED | `metrics.new_customers` |
| Total users, active users, and period new users KPI | IMPLEMENTED | `metrics.total_users`, `metrics.active_users`, `metrics.new_users` |
| Period new-request KPI | IMPLEMENTED | `metrics.new_requests` |
| Period-aware KPI refresh after changing filter | IMPLEMENTED | KPI cards use `data-metric` identifiers and are refreshed from selected period response |
| Period-scoped request count | IMPLEMENTED | `metrics.requests_in_period` |
| Period-scoped request trend | IMPLEMENTED | `requests_trend` |
| Period-scoped request status distribution | IMPLEMENTED | `requests_by_status` |
| Period-scoped requests by service | IMPLEMENTED | `requests_by_service` |
| Service-scoped recent requests | IMPLEMENTED | `recent_requests` uses the selected service scope |
| Service performance panel | IMPLEMENTED | `#periodServiceChart` |
| Operations summary for overdue requests and pending quotations | IMPLEMENTED | `#periodOperations` |
| Actionable overdue request queue | IMPLEMENTED | `overdue_items`, opens Requests list filtered by title |
| Actionable pending quotation queue | IMPLEMENTED | `pending_quotation_items`, opens related request in Requests list |
| Loading, error, and retry states for period analytics | IMPLEMENTED | `dashboard-period-analytics.js` |
| Service filter is reflected in recent requests table | IMPLEMENTED | Selected-service response refreshes recent request rows |
| Service filter API contract | IMPLEMENTED | `tests/test_admin_console.py` |
| Period analytics script is loaded after authenticated dashboard initialization | IMPLEMENTED | `loadDashboard()` invokes `window.refreshDashboardPeriodAnalytics()` |
| Reporting period API contract and bounds tests | IMPLEMENTED | `tests/test_admin_console.py` |
| Static analytics asset delivery test | IMPLEMENTED | `tests/test_admin_console.py` |

## Remaining work before Module 01 can be VERIFIED

1. Run backend test suite in the repository's supported isolated test environment and record the exact result. The current GitHub commit has no Actions run; Vercel reports a build-rate-limit failure, and a new preview deployment request was blocked by the Vercel 100-deployments-per-day API quota.
2. Add authenticated integration tests that seed isolated users, requests, services, quotations, and audit events; verify aggregate counts and date-window boundaries. The current tests verify the OpenAPI contract, authentication, and static asset delivery only.
3. Verify date/time behavior across the configured platform timezone and UTC storage conventions.
4. KPI cards for customers, users, requests, staff, and services now open their existing permission-protected lists. Contextual filtered drill-down from charts, service rows, and operational alerts remains outstanding.
5. Add global dashboard filters for service and supported organization scope only after authoritative scope data and policies exist.
6. Audit Trail now has bounded text search and 25-record pagination; the dashboard's ten-event recent-activity preview still needs its own filtering/drill-down behavior and browser verification.
7. Implement persisted per-user dashboard preferences and a complete notification center only after the required durable preference/read/delivery models and permission contracts are confirmed. The current User model has no dashboard-preference fields; Notification has no read timestamp or delivery-attempt model, so these workflows remain blocked on a reviewed schema/migration design.
8. Add loading, empty, retry, and permission-denied states for each dashboard panel, including the new analytics extension.
9. Dashboard detail collections are now permission-scoped (`requests:read`, `quotes:read`, `audit:read`, `services:read`). The dashboard route itself still uses the coarse `admin:access` gate; introduce a dedicated `dashboard:read` permission only with a safe permission-seeding/rollout plan so existing administrators are not locked out.
10. Run browser-level checks for desktop/tablet/mobile, Arabic/English, RTL/LTR, light/dark, keyboard access, and chart text alternatives.
11. Measure aggregate query performance and add indexes only when justified by query plans and measured access patterns.
12. Record acceptance evidence and update this status to `VERIFIED` only after all required checks pass.

## Additional security hardening in this delivery slice

- Dashboard overview now derives the authenticated user's effective permission codes from the persisted RBAC relationships.
- Recent request rows and overdue request details are returned only to users with `requests:read`.
- Pending quotation details are returned only to users with `quotes:read`.
- Recent audit activity is returned only to users with `audit:read`.
- Service selector options and service-name analytics are returned only to users with `services:read`.
- Aggregate dashboard metrics remain under the dashboard's existing `admin:access` gate; the detail collections above are separately permission-scoped.
- Status: `IMPLEMENTED`; automated behavior tests and browser verification are still required before this can be marked `VERIFIED`.

## Global search delivery slice

- Added a global search control to the administration top bar.
- Search reuses the existing users, services, and requests list APIs; it does not create a parallel search data source.
- Each result category is queried only when the current session's effective permissions include the corresponding `users:read`, `services:read`, or `requests:read` permission.
- Selecting a result opens the corresponding existing management page with its search field populated.
- Loading, no-result, insufficient-permission, keyboard Escape/Enter, and responsive dropdown behavior are implemented.
- Status: `IMPLEMENTED`; automated tests and browser-level behavior are not yet executed, so this is not `VERIFIED`.

## Audit activity search and pagination slice

- Extended the existing audit-log API with bounded text search across action, resource type, and description.
- Replaced the total-count query that loaded every matching audit ID with a database-side count aggregate.
- Added search input and 25-record previous/next pagination controls to the Audit Trail screen.
- Existing `audit:read` backend authorization remains mandatory; search does not bypass it.
- Added OpenAPI-bound and unauthenticated-access regression checks.
- Status: `IMPLEMENTED`; the tests and browser interaction still need execution before `VERIFIED`.

## KPI drill-down slice

- KPI cards for customers, users, requests, staff, and services now open their existing management lists.
- Drill-down affordances are rendered only when the current user has the corresponding read permission.
- Cards support pointer and keyboard activation and do not invent filters or expose inaccessible pages.
- Status: `IMPLEMENTED`; browser and permission-matrix verification remain outstanding.

## Dashboard quick actions slice

- Added a compact quick-action row below the welcome panel.
- Actions link to existing Requests, Services, Users, Audit Trail, and Settings pages.
- Each action is rendered only when the session has the corresponding backend permission.
- The actions reuse existing routes and do not create fake create/edit workflows.
- Status: `IMPLEMENTED`; responsive browser and permission-matrix verification remain outstanding.

## CI diagnostics (2026-11-06)

- The existing `Python tests` workflow ran on PR #11 and reported **33 passed, 1 failed**. The failure was the new audit-search test assuming OpenAPI emitted `maxLength` at a specific schema path; the test now checks the runtime 201-character request rejection (HTTP 422) instead.
- The newly added `Phase 01 verification` workflow initially failed before tests because `pip install -e ".[dev]"` triggered setuptools flat-layout package discovery across multiple top-level folders. The workflow was corrected to use the repository's locked `uv sync --locked --all-groups --all-extras` path.
- A rerun after these corrections is not yet available in the retrieved Actions evidence. Do not interpret Vercel's successful Preview deployment as a passing Python test suite.
- Latest Vercel Preview for commit `cfe898307578e3b0411a12c2f990af867ca5f9c4` reached `READY`; it is a Preview deployment, not Production.

## Validation status

- One GitHub Actions test run was observed: 33 passed, 1 failed; its assertion has been corrected, but a passing rerun is not yet evidenced.
- The Phase 01 verification workflow is configured to use the locked project environment; its first dependency-install attempt failed and was corrected. Await the rerun before claiming a pass.
- Vercel Preview deployment for the latest corrected test commit reached `READY`; this confirms deployment build only, not backend test success or browser acceptance.
- No browser session or end-to-end visual acceptance has been executed from this remote GitHub editing session.

## Safety

- No production database was accessed or modified.
- No production deployment or Vercel configuration was changed.
- No branch merge or pull request merge was performed.
- Existing dashboard and legacy admin routes were retained.
