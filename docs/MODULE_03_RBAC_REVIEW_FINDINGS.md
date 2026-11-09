# Module 03 — RBAC Integration Review Findings

**Review date:** 2026-11-09  
**Branch:** `feature/module-03-rbac-phase-zero`  
**Status:** Static source review only — not runtime verified.

This note records concrete integration gaps found while reviewing the current Module 03 implementation. It does not change application behavior or claim acceptance.

## Finding 01 — Custom roles in user creation (addressed in current branch; tests not run)

**Location:** `backend/app/api/routes/admin_users.py`, `AdminUserCreateRequest` and `create_admin_user`.

The RBAC implementation now supports custom roles through:
- `POST /api/v1/rbac/roles`
- `PUT /api/v1/admin/users/{user_id}/role`
- `PUT /api/v1/admin/users/{user_id}/roles`

However, the existing user-creation workflow still parses `payload.role` through `RoleName`, whose enum contains only the six canonical roles. It therefore rejects a valid custom role name even when that role already exists in the database.

**Impact:** An administrator must create a user first with a canonical role and then make a second API call to assign the intended custom role. This is an inconsistent and incomplete end-to-end workflow; it is not a bypass of the newer assignment endpoint.

**Required correction:**
1. Resolve the requested role from the database by normalized role name instead of restricting creation to `RoleName`.
2. Apply the same grantor rules as the governed assignment endpoints:
   - the operator cannot grant permissions outside their own effective permission set;
   - assigning `super_admin` or a role containing `roles:manage` is Super-Admin-only;
   - preserve existing user-creation validation and audit behavior.
3. Keep the existing default `customer` role for backward compatibility.
4. Add API integration tests for custom-role creation, unknown role rejection, privilege-boundary rejection, Super-Admin-only governance assignment, and audit metadata.

Do not solve this by trusting a client-supplied role ID or by weakening the checks in the governed assignment endpoints.

## Finding 02 — Authorization helper implementations still have different sources of truth

**Locations:**
- `backend/app/modules/authentication/authorization.py` uses the hardcoded `ROLE_PERMISSIONS` mapping.
- `backend/app/modules/authentication/rbac.py` evaluates database-backed `role.permissions`.
- `backend/app/api/rbac_dependencies.py` independently evaluates database-backed permission codes.

**Impact:** A custom role can be represented in the database but is not represented in the canonical `RoleName` enum / `ROLE_PERMISSIONS` mapping. Any business code that still calls the hardcoded helper may therefore disagree with the API authorization dependency.

**Required correction:**
1. Complete a repository-wide call-site inventory for both helper modules.
2. Classify each call site by runtime path and whether it receives freshly loaded role relationships.
3. Add parity tests for canonical roles and explicit custom-role tests for database-backed paths.
4. Only then consolidate or deprecate a helper. Do not change authorization behavior based solely on static inspection.

## Verification boundary

- These are findings from source inspection, not reproduced runtime failures.
- No test suite was executed as part of this review.
- No browser acceptance was performed.
- No database migration, production database access, secrets change, merge, or deployment was performed.
- Keep PR #34 in Draft until the fixes and isolated automated/browser acceptance evidence are complete.


## Finding 03 — Existing sessions after role-permission changes (addressed in current branch; tests not run)

**Location:** `backend/app/api/routes/rbac_admin.py`, `update_role_permissions`.

A permission-set change now revokes all non-revoked sessions belonging to users assigned the affected role in the same database transaction as the permission update. The audit event records the number of sessions revoked.

This is deliberately scoped to sessions of users who currently hold the changed role. It does not revoke sessions for unrelated users or for no-op permission updates.

**Test added:** `test_rbac_permission_change_revokes_sessions_for_users_with_the_role` checks that the route issues the session-revocation update and records its row count in the audit metadata.

**Verification:** Source and test changes only. The test has not been executed; database-engine behavior and full API integration remain unverified.


## Finding 04 — RBAC overview API was not surfaced in the dashboard (addressed in current branch; tests not run)

**Locations:** `backend/app/api/routes/rbac_admin.py`, `backend/app/static/admin/console.html`, and `backend/app/static/admin/console.js`.

The database-backed `GET /api/v1/rbac/overview` endpoint already returned role totals, system/custom role counts, permission catalogue size, users with roles, and recent RBAC changes. The Roles & Permissions page did not call or display that endpoint.

The current branch adds a responsive overview metric row to the existing page and loads the six available values from the API. If the overview request fails, the role list and permission editor remain usable and the metric values show the existing unavailable state rather than blocking the whole page.

**Test added:** `test_rbac_dashboard_renders_database_backed_overview_metrics` verifies the dashboard container, API call, and displayed metric fields.

**Verification:** Static source assertions only; not executed. Browser layout, localization rendering, and live API integration remain unverified.
