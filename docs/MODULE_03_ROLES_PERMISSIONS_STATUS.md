# Module 03 — Roles & Permissions (RBAC): Status and Gap Analysis

**Repository:** `MoatasemTAlmasani/academic-telegram-platform`  
**Baseline inspected:** `main` plus the unmerged roadmap branch `docs/module-03-rbac-roadmap-details`  
**Working branch:** `feature/module-03-rbac-phase-zero`  
**Inspection date:** 2026-11-09  
**Phase:** 03.1 — Inventory and Gap Analysis  
**Overall status:** `PARTIAL`  
**Production/database changes:** None  
**Tests executed during this inspection:** None

> This report records a remote source inspection. It does not claim local working-tree inspection, runtime/browser verification, test execution, production verification, or database inspection. Statuses distinguish source evidence from verified runtime behavior.

## 1. Executive summary

EHTERAF already has a database-backed RBAC foundation and an existing administration UI. It must be extended, not replaced.

Confirmed existing elements include:
- SQLAlchemy `Role` and `Permission` models and many-to-many `user_roles` / `role_permissions` tables.
- Six canonical role names and a Python permission enum/catalog.
- Database-backed permission checks through `require_permission`.
- Existing role and permission read APIs and a role-permission replacement API.
- Existing single-role assignment API, account access summary, session revocation, and audit logging.
- One Roles & Permissions page embedded in the existing admin console, plus user-detail effective-access display and a general audit page.

The current implementation is therefore **PARTIAL**, not absent. The principal gaps are custom role lifecycle, complete multi-role assignment workflows, robust grant-authority rules, richer catalog metadata and filtering, dedicated RBAC workflows/pages, effective-access diagnostics, specialized audit filters/export controls, and comprehensive security/concurrency evidence.

## 2. Authoritative documents inspected

| Document | Inspected ref | Finding |
|---|---|---|
| `docs/ROADMAP.md` | `docs/module-03-rbac-roadmap-details` | Contains the expanded Module 03 scope and eight workflows from PR #33. |
| `docs/ADMIN_SYSTEM_DELIVERY_BLUEPRINT.md` | `main` and roadmap branch | Requires database-backed RBAC, backend enforcement, audit, localization, isolated tests, and evidence-based VERIFIED status. |
| `docs/EHTERAF_MASTER_REFERENCE.md` | `main` and roadmap branch | Confirms FastAPI modular monolith, Arabic/English, RTL/LTR, no Firebase, and no speculative multi-tenancy. |

PR #33 is still open and unmerged at the time of inspection. The roadmap branch is used as the base for this working branch so the detailed scope is retained. This report does not merge PR #33 or change `main`.

## 3. Existing backend architecture

### 3.1 Models and relationships

Source: `database/models/identity.py`

- `User` has a many-to-many `roles` relationship through `user_roles`.
- `Role` has a unique `name`, optional `description`, and relationships to users and permissions.
- `Permission` has a unique `code`, optional `description`, and a relationship to roles.
- `role_permissions` is a many-to-many association table.
- `UserSession` stores server-side sessions with expiry and revocation fields.
- Existing `AuditLog` is used by privileged operations.

Current schema does **not** expose role active/system classification, bilingual role fields, or permission module/resource/action/sensitivity/localization fields. Do not add these automatically; first determine whether they are necessary and whether existing metadata/translation conventions can supply them.

### 3.2 Permission definitions and role constants

Source:
- `backend/app/modules/authentication/permissions.py`
- `backend/app/modules/authentication/roles.py`

The current permission enum contains these 30 codes:

```text
users:read       users:create       users:update       users:delete
services:read    services:create    services:update    services:delete
requests:read    requests:create    requests:update
files:read       files:upload       files:delete
quotes:read      quotes:create      quotes:update
content:read     content:create     content:update     content:delete
campaigns:read   campaigns:create   campaigns:update   campaigns:delete
telegram:read    telegram:manage
audit:read
admin:access
roles:manage
```

The canonical roles are `super_admin`, `admin`, `manager`, `staff`, `support`, and `customer`. Python `ROLE_PERMISSIONS` defines canonical permission sets, while the API authorization dependency reads the permissions attached to database role objects. This dual representation is an architectural risk until seeding, synchronization, and runtime usage are traced end-to-end. Do not assume either source can be removed.

Existing codes use the two-part `resource:action` style. Preserve them for compatibility; the proposed `module:resource:action` format must not trigger a bulk rename.

### 3.3 Authorization dependency

Source: `backend/app/api/rbac_dependencies.py`

`require_permission(permission)` obtains the current authenticated user, iterates their assigned roles and each role's database permissions, and returns 403 when the required code is not present.

This is genuine backend enforcement for routes that use the dependency. It does not by itself prove that every protected route in the whole application uses it, or that cached/session-loaded role relationships are refreshed correctly after every change.

### 3.4 Existing RBAC APIs

Source: `backend/app/api/routes/rbac_admin.py`

| Capability | Existing API | Current authorization |
|---|---|---|
| List roles with permissions | `GET /rbac/roles` | `admin:access` |
| List registered permissions | `GET /rbac/permissions` | `admin:access` |
| Replace a role's permission set | `PUT /rbac/roles/{role_id}/permissions` | `roles:manage` |

The permission-update endpoint currently:
- Locks the role row with `with_for_update()`.
- Rejects a missing role.
- Protects the role whose name is `super_admin`.
- Reserves `roles:manage` for `super_admin`.
- Rejects unknown permission codes.
- Replaces the permission relationship and writes before/after values to `AuditLog`.
- Commits only when the set changes.

Limitations to address/test:
- No custom role create/update/duplicate/activate/deactivate lifecycle is exposed in this route file.
- Read APIs use broad `admin:access`; confirm whether this matches the intended read policy without conflating it with mutation authority.
- The route checks the target role by its name; protection must be reviewed against the canonical/system-role invariant.
- Grantor authority is currently narrower only for the reserved `roles:manage` code; the general rule that an operator cannot grant permissions outside their own authority needs explicit review.
- Concurrency behavior and rollback must be tested on supported database engines; row-lock behavior is not equivalent on every test backend.

### 3.5 User role assignment and effective access

Source: `backend/app/api/routes/admin_users.py`

Existing capabilities include:
- Paginated/searchable user directory with role filtering.
- Account create/update/lifecycle routes.
- `PUT /admin/users/{user_id}/role` to assign one canonical role.
- A read-only `GET /admin/users/{user_id}/access-summary` returning assigned roles and the union of their database permission codes.
- Session revocation when a user's role is changed.
- Audit records for role changes.
- Self-role-change protection and last active admin/Super Admin checks in relevant account/role flows.

Important limitation: although the database relationship supports multiple roles, the current role-assignment endpoint deliberately replaces the user's roles with exactly one canonical role. The requested multi-role assignment workflow is therefore not implemented end-to-end. Any extension must preserve existing API compatibility and review all account-creation, bulk lifecycle, role-change, session, and audit paths.

The last-admin helper locks canonical role rows before counting active users. Its correctness under simultaneous removal/demotion attempts, across the production database engine and transaction boundaries, is **not verified by this read-only inspection**.

### 3.6 Audit API

Source: `backend/app/api/routes/admin_audit.py`

An existing audit list endpoint provides server-side limit/offset pagination and filters for action, free-text search, resource type, actor, and time range. It requires `audit:read`.

RBAC permission updates and user-role changes write to the existing `AuditLog`; no parallel audit system is needed. A dedicated RBAC audit view, event outcome/correlation metadata coverage, export authorization, and denied-operation coverage remain to be verified or implemented.

## 4. Existing frontend and navigation

Sources:
- `backend/app/static/admin/console.html`
- `backend/app/static/admin/console.js`

The current application serves an existing admin console; no separate RBAC application is required.

Confirmed UI:
- A Roles & Permissions navigation item exists inside the User & Account Management submenu.
- It is currently gated in navigation by `admin:access`.
- A `page-roles` screen displays platform roles and a role detail panel.
- The page has an existing role list and permission editing UI backed by the existing APIs.
- User details show assigned roles and effective permissions.
- The account detail screen contains a single canonical role selector for assignment.
- A general audit page already exists.
- The console has Arabic/English dictionaries and existing theme/direction behavior.

The current page is one consolidated roles/permissions page, not the eight requested dedicated workflows. The exact completeness of all UI states, keyboard accessibility, and responsive behavior has not been browser-tested in this inspection.

## 5. Requirement status matrix

Status meanings: NOT_STARTED / IN_PROGRESS / PARTIAL / IMPLEMENTED / VERIFIED / BLOCKED.

| Requirement | Status | Evidence / gap |
|---|---|---|
| Existing role and permission models | IMPLEMENTED | Existing SQLAlchemy models and association tables. |
| Permission catalog and canonical codes | PARTIAL | 30 enum codes and DB records model; metadata, integrity/sync and full UI filters need verification. |
| Backend permission dependency | IMPLEMENTED | DB-role permission lookup in `require_permission`; whole-platform route coverage not audited. |
| Role list/detail read | PARTIAL | List API exists; dedicated detail and robust pagination/filtering not confirmed. |
| Custom role lifecycle | NOT_STARTED | No lifecycle endpoints confirmed in inspected RBAC route file. |
| Role-permission replacement | PARTIAL | Existing transactional/audited endpoint; grantor boundary, conflict semantics and concurrency tests need proof. |
| User-role assignment | PARTIAL | Existing single canonical role replacement; requested multi-role workflow absent. |
| Effective permission summary | PARTIAL | Existing read-only summary; permission source mapping and diagnostic access check absent/not confirmed. |
| Last active Super Admin protection | PARTIAL | Existing helper and role-change checks; concurrent invariant not proven. |
| Session invalidation after role change or permission change | IN_PROGRESS | Role assignment revokes sessions; the current branch now also revokes sessions for users assigned a role when its permission set changes. Runtime verification remains outstanding. |
| RBAC audit records | PARTIAL | Existing audit writes and general list endpoint; full RBAC event/outcome/export workflow incomplete. |
| Eight dedicated RBAC workflows | PARTIAL | Existing combined role page, user access summary and general audit; no evidence of all eight. |
| Arabic/English and RTL/LTR | PARTIAL | Existing dictionaries and layout behavior; complete RBAC coverage not verified. |
| Responsive/accessibility acceptance | NOT_STARTED | No browser/device evidence captured in this inspection. |
| Backend/security/integration tests | PARTIAL | Test implementation inventory and execution still required. |
| Documentation and acceptance evidence | IN_PROGRESS | This status report is being established; implementation evidence not yet available. |

No item is marked VERIFIED in this report.

## 6. Existing tests and CI

The current repository test inventory and workflow configuration were not completely resolved through this remote file inspection. No tests were executed. Therefore:
- Do not interpret the absence of test paths in this report as proof that tests do not exist.
- Before implementation, locate the current RBAC, admin-user, authentication, session, audit, frontend, and CI tests in the repository.
- Run only isolated test configurations; verify database URLs and fixture setup before executing.
- Never point tests or migrations at production or at the protected local/production database.

Required test coverage is listed in the approved Module 03 roadmap and should be mapped to existing tests before adding new ones.

## 7. Risks and architectural constraints

1. **Dual authorization representation:** database role-permission relationships and Python `ROLE_PERMISSIONS` constants coexist. Trace seed/update/authentication usage before changing either.
2. **Single-role API contract:** the current user-role endpoint replaces the role set. Multi-role support must be additive and compatibility-tested.
3. **Privilege boundary:** reserving `roles:manage` is not equivalent to enforcing a complete grantor authority boundary.
4. **Last Super Admin concurrency:** existing row locks/counts require database-engine-specific concurrent tests and transaction review.
5. **Stale authorization:** role changes revoke sessions in one path; permission matrix changes do not visibly revoke all affected sessions in the inspected RBAC route.
6. **Role lifecycle schema:** active/system/bilingual metadata is not present on the inspected `Role` model. Avoid speculative columns and preserve legacy role identifiers.
7. **Frontend coupling:** the admin console is a static HTML/JS application. Follow its current conventions; do not introduce a new frontend framework.
8. **Scope model:** organization/branch scope is not established by this module. Do not invent scope tables or enforcement.
9. **Remote inspection limitation:** uncommitted Codespaces work is not visible through GitHub. Reconcile the local working tree before any merge or deployment.

## 8. Implementation plan

### 03.1 — Inventory and gap analysis
- Complete local working-tree/branch reconciliation before any local edits.
- Locate all relevant test files, seeders, API registration, permission checks, auth/session loading, and frontend event handlers.
- Map every protected API to its permission requirement.
- Finalize this report with exact test paths and CI workflows.

### 03.2 — Roles management
- Add custom role lifecycle only after checking role seeding and compatibility constraints.
- Preserve the six canonical roles and protect system roles using stable identity/classification, not display-name assumptions.
- Add validation, duplicate-code/name handling, impact preview, audit, and tests.

### 03.3 — Permission catalog and matrix
- Treat registered database permission codes as authoritative at runtime, reconcile seed constants safely.
- Add metadata through existing catalog/i18n patterns where possible.
- Add safe grouping/filtering, before/after preview, dirty state, conflict handling, and transaction tests.
- Preserve all existing permission codes.

### 03.4 — User-role assignment
- Reconcile single-role legacy API with multi-role relationship support.
- Enforce grantor authority, no self/indirect escalation, inactive-role policy if supported, and last Super Admin invariant.
- Preserve existing session revocation and audit semantics.

### 03.5 — Effective permissions and security
- Reuse the existing access summary; add source-role mapping and read-only diagnostics based on the real authorization evaluator.
- Define and test permission refresh/revocation behavior after grants and revocations.
- Prove IDOR, cross-scope (only if scopes exist), and concurrent Super Admin protections.

### 03.6 — Audit and dashboard integration
- Reuse `AuditLog` and existing admin shell.
- Deliver the eight required navigation workflows as integrated pages/views, without duplicating user/audit capabilities.
- Complete Arabic/English, RTL/LTR, responsive and accessible states.

### 03.7 — Verification and acceptance
- Run mapped backend, API, security, concurrency, frontend, and integration tests on isolated databases.
- Record actual commands, results, CI run links and browser evidence.
- Mark only evidence-backed requirements VERIFIED.

## 9. Initial affected-file map

| Area | Existing files to inspect/extend |
|---|---|
| Models | `database/models/identity.py`, `database/models/audit.py` |
| Permission definitions | `backend/app/modules/authentication/permissions.py`, `roles.py` |
| Authorization | `backend/app/api/rbac_dependencies.py`, `backend/app/api/auth_dependencies.py` |
| RBAC API | `backend/app/api/routes/rbac.py`, `rbac_admin.py` |
| User-role and access summary | `backend/app/api/routes/admin_users.py` |
| Audit API | `backend/app/api/routes/admin_audit.py` |
| Frontend | `backend/app/static/admin/console.html`, `console.js`, associated stylesheet and localization dictionaries |
| Tests/CI | Exact paths to be added after repository test inventory; no paths inferred here |
| Documentation | `docs/MODULE_03_ROLES_PERMISSIONS_STATUS.md`, `docs/ROADMAP.md`, `docs/ADMIN_SYSTEM_DELIVERY_BLUEPRINT.md` |

## 10. Test strategy

- First inspect test fixtures and database configuration; assert that the configured database is isolated before running tests.
- Unit-test permission evaluation and grant-authority policy.
- API-test anonymous, unauthorized, authorized, invalid IDs, unknown permissions, and validation failures.
- Test transactional rollback and concurrent matrix edits on the supported database engine.
- Test concurrent attempts to remove/demote the last active Super Admin.
- Test multi-role effective permission union and compatibility of the legacy single-role endpoint.
- Test session invalidation/refresh after role and permission changes.
- Test audit event completeness and safe metadata.
- Test all RBAC UI workflows in Arabic/English, RTL/LTR, responsive viewports and loading/empty/error/denied/conflict states.
- Compare UI effective permissions with backend authorization decisions using the same test identities and isolated fixtures.

## 11. Safety and rollback

- No production DB, records, environment variables, secrets, or deployment settings were accessed or changed by this inspection.
- No migration was run.
- No application code was changed in Phase Zero.
- The report is committed on a feature branch based on the unmerged roadmap branch; `main` remains unchanged.
- Any future schema change requires a reversible Alembic migration and isolated-database tests.
- Roll back code through the feature branch/PR; do not reverse production data manually. Database rollback must follow the reviewed migration plan and must never be run against production without separate explicit authorization.

## 12. Phase 03.1 exit status

**Status: IN_PROGRESS**

Completed: remote source inspection of the three approved architecture documents, RBAC models, permission/role definitions, authorization dependency, RBAC admin routes, admin-user RBAC flows, audit API, and admin-console navigation/page markup.

Remaining before declaring 03.1 complete:
- Reconcile local uncommitted work in Codespaces (not visible to this remote inspection).
- Locate and map exact test files and CI workflows.
- Inspect API router registration and seed/synchronization logic.
- Trace authentication user loading and role-permission refresh behavior.
- Inspect the full frontend role-page JavaScript handlers and stylesheet behavior.
- Execute the isolated relevant test suite and record real results.

**Next sub-phase safety:** Do not begin schema changes or role lifecycle implementation until the remaining inventory items above are resolved. Non-destructive test discovery and code-path tracing can proceed safely.


## 13. Follow-up repository trace (2026-11-09)

The recursive Git tree and source files were inspected after the initial report was committed. This resolves several items that were previously listed as pending discovery.

### 13.1 Router registration

- `backend/app/api/router.py` imports and registers both `rbac_router` and `rbac_admin_router` under the existing `/api/v1` API router.
- Both routers use the `/rbac` prefix, so their paths coexist as intended; no additional router registration is required.

### 13.2 Test inventory found

- `tests/test_rbac_admin_security.py`: role-permission row-lock assertion, Super Admin protection, reserved `roles:manage`, audit before/after payload, no-op behavior, and a frontend permission-edit visibility assertion.
- `tests/test_rbac_roles.py`: six canonical roles, least-privilege matrices, copy isolation, seed/runtime matrix parity, and an in-memory SQLite migration upgrade/downgrade preservation test.
- `tests/test_admin_users_security.py`: admin-user route authentication/permission matrix, permission dependency behavior, session ownership checks, and lifecycle safeguards.
- `tests/test_admin_users_api_integration.py`: existing admin-user API integration coverage.
- `tests/test_postgres_concurrency.py`: isolated PostgreSQL concurrency acceptance test for concurrent admin deactivation. It requires `PHASE_ACCEPTANCE_DATABASE_URL` to point to a local disposable database named exactly `phase_acceptance`; it drops/recreates schema in that database. It does not currently prove concurrent removal/demotion of the last `super_admin` role assignment.
- `tests/test_admin_console.py`: admin console test coverage.

### 13.3 CI workflows found

- `.github/workflows/python-tests.yml`: Python 3.12, locked dependencies, full pytest suite. Its configured PostgreSQL URL is explicitly described as import-time configuration; tests inject fakes and do not connect.
- `.github/workflows/phase-01-verification.yml`: Python 3.12, isolated PostgreSQL 16 service, dedicated `ehteraf_test` and `phase_acceptance` databases, compileall and full pytest suite. The workflow creates the disposable `phase_acceptance` database before tests.

These workflows were inspected but not executed by this remote inspection.

### 13.4 Authentication and authorization refresh

- `backend/app/api/auth_dependencies.py` validates the JWT-bound server-side `UserSession` on every authenticated request, rejects revoked/expired sessions, and loads the user through `UserService.get_by_id`.
- `backend/app/api/rbac_dependencies.py` checks the current user's loaded database `roles[*].permissions[*].code` on each protected request.
- `backend/app/modules/authentication/rbac.py` is a second database-backed permission helper.
- `backend/app/modules/authentication/authorization.py` is a separate helper that resolves permissions through the hardcoded `ROLE_PERMISSIONS` mapping by role name rather than database permission relationships.

This confirms two different authorization evaluation strategies exist. The exact production call sites of both helpers must be mapped before changing or consolidating them. The FastAPI permission dependency itself is database-backed and receives a freshly loaded user through the current-user dependency. Existing role changes revoke sessions in the admin-user route. The role-permission update route does not visibly revoke all sessions of users assigned to the changed role, but because permission checks read the loaded user's current database relationships this requires runtime/session identity-map tests rather than assumption.

### 13.5 Schema constraints confirmed

- `Role` has only `id`, timestamps, unique `name`, optional `description`, users and permissions relationships.
- `Permission` has only `id`, timestamps, unique `code`, optional `description`, and roles relationship.
- There is no role active flag, system-role flag, bilingual role-name/description pair, permission module/resource/action/sensitivity metadata, or direct user-permission table.
- The six canonical roles are seeded by `database/migrations/versions/aa77bb88cc99_seed_six_rbac_roles.py`; the migration snapshots existing role descriptions and permission links before changing canonical seed data and restores them on downgrade.
- Existing role assignment endpoint in `admin_users.py` replaces the user's roles with one canonical role and revokes active sessions. The underlying many-to-many model supports multiple roles, but the existing API/UI contract does not expose multiple assignments.

### 13.6 Revised Phase 03.1 status

Repository-level source discovery is now substantially complete. Remaining checks that cannot be honestly marked complete from static GitHub source inspection:
- Full local working-tree reconciliation (not visible through the GitHub connector).
- Runtime execution of the mapped tests and CI workflows.
- Database-engine concurrency proof for Super Admin role removal/demotion.
- Browser verification of all requested eight workflows and responsive/RTL/LTR states.
- Complete call-site map for both authorization helper implementations.

**Phase 03.1 remains PARTIAL pending executable verification and local-state reconciliation.** No test results are claimed.


## Phase 03.2 — First implementation slice (in progress)

**Implemented in this branch; not yet runtime-verified:**

- Added `POST /api/v1/rbac/roles` to create a custom role using the existing `roles` table and its current `name` / `description` fields. No migration or new model fields were introduced.
- Custom role names are normalized to lowercase snake_case, bounded in length, and prevented from using the six canonical system-role names.
- Creation requires the existing `roles:manage` permission, handles duplicate-name conflicts, and writes a `rbac.role_created` audit event.
- Extended the existing user-role assignment request to accept an existing custom role name as well as the canonical names. Assignment remains protected by `roles:manage`, locks the target user and selected role, preserves the existing self-change / last-Super-Admin protections, records before/after roles, and revokes active sessions.
- Added a bilingual Arabic/English custom-role creation form to the existing Roles & Permissions screen. The form is rendered only when the signed-in operator has `roles:manage`; it calls the new API and opens the created role for permission configuration.
- Added focused unit-level coverage, a static UI authorization assertion, and an isolated SQLite API integration scenario for custom-role creation, audit, assignment, and session revocation.

**Verification status:** `PARTIAL / NOT VERIFIED`. Tests were added but have not been executed in this environment. The current PR base is not `main`, and the inspected CI workflows trigger PR runs only when targeting `main`; therefore no CI run is expected from the current draft PR target. No production database, production data, secrets, or deployment were accessed or changed.

**Remaining for this slice:** execute the targeted and full test suites in CI or an isolated development environment; inspect the resulting workflow logs; complete browser acceptance coverage for the create-role form and permission-assignment workflow. Custom-role permission assignment is already supported by the existing permission-matrix endpoint, subject to the same `roles:manage` authority and existing protection against granting `roles:manage` to non-Super-Admin roles.


### Phase 03.2 security and acceptance-test additions

- Extracted the last-active-Super-Admin demotion check into a focused helper. Every demotion now locks the canonical `super_admin` role row before counting active holders, so concurrent role changes serialize on the same database row.
- Added a PostgreSQL-only concurrency acceptance test that runs two simultaneous Super Admin demotions against the dedicated disposable database `phase_acceptance`; it expects exactly one demotion to succeed and one to be rejected, leaving one active Super Admin.
- Strengthened the isolated SQLite API integration test to create a live session for the target user and assert that role assignment revokes that session.
- Strengthened duplicate-name coverage to include a pre-existing uppercase role name, verifying the case-insensitive lookup behavior.

These tests are authored but have **not** been executed. The PostgreSQL acceptance test is guarded by the existing strict local-database-name/host checks and must never be pointed at production or a shared application database.


## Phase 03.3 — Custom role metadata management (in progress)

- Added `PATCH /api/v1/rbac/roles/{role_id}` for custom-role rename and description updates.
- The endpoint requires `roles:manage`, locks the role row, rejects edits to all six canonical system roles, rejects reserved system names and case-insensitive duplicates, and validates partial updates without accepting unexpected fields.
- Changed metadata is recorded in the existing `AuditLog` with explicit before/after values; no-op updates do not create audit noise.
- Added a bilingual Arabic/English metadata editor to the existing Roles & Permissions screen. It is only rendered for custom roles when the operator has `roles:manage`.
- Extended unit and isolated SQLite API integration coverage for metadata updates, system-role protection, duplicate-name conflicts, and the create → update → assign → session-revocation workflow.

**Verification remains PARTIAL / NOT VERIFIED:** these tests have been authored but not executed. Browser acceptance is also pending.


### Phase 03.4 — Grantor privilege-boundary enforcement (in progress)

- Role-permission updates now reject any requested permission that is not already present in the operator's effective permission union, even when the operator has `roles:manage`.
- User-role assignment now loads the target role's permissions and rejects assignments that would grant permissions beyond the operator's own effective access.
- Assigning the canonical `super_admin` role, or any role carrying `roles:manage`, is restricted to an operator who already holds the canonical `super_admin` role.
- Added focused negative tests for unauthorized permission grants, over-privileged role assignments, and non-Super-Admin attempts to assign the Super Admin role.

This closes an important privilege-escalation gap in the earlier implementation slice. Automated tests remain authored but unexecuted; the change is not yet verified.


### Phase 03.5 — Safe custom-role duplication (in progress)

- Added `POST /api/v1/rbac/roles/{role_id}/duplicate`.
- Duplicating the protected `super_admin` role is rejected. Other role templates may be copied into a new custom role with a caller-supplied normalized name.
- The duplicate copies only source permissions that are within the operator's own effective permission set; `roles:manage` is always excluded from the copy.
- The operation is audited with source/target role identifiers and copied/excluded permission codes. It uses the existing `Role`, `Permission`, and `AuditLog` models without migrations.
- Added a bilingual duplicate-role form and extended unit/API integration coverage for the copy rules and privilege boundaries.

**Verification remains PARTIAL / NOT VERIFIED:** no automated test or browser run has been executed in this environment.


### Phase 03.6 — Multi-role user assignment (in progress)

- Added a backward-compatible `PUT /api/v1/admin/users/{user_id}/roles` endpoint. The original single-role endpoint remains available for existing clients.
- The new endpoint validates and normalizes role-name sets, loads all requested roles and their permission records, computes the union of effective permissions, enforces the grantor's privilege boundary, protects Super Admin/RBAC-governance assignment, blocks self-escalation, and preserves the last-active-Super-Admin invariant.
- Role-set changes revoke the target account's active sessions and write before/after role names to the existing audit log. Empty role sets are supported for explicit access removal; the final active Super Admin remains protected.
- Replaced the account-detail single-role selector with a responsive, permission-gated multi-role picker populated from the persisted role directory. The existing access summary displays the resulting effective permission union.
- Added unit and isolated SQLite API integration coverage for multi-role assignment, permission union, session revocation, and grantor-boundary rejection.

**Verification remains PARTIAL / NOT VERIFIED:** automated tests and browser acceptance have not been run.


### Phase 03.7 — Effective access respects account eligibility (in progress)

- Extended the read-only access-summary response with account status, an explicit `access_enabled` flag, and a safe block reason.
- Effective permissions are now empty when the target account is inactive, temporarily locked, or expired, matching the checks used by the authenticated-request dependency. Assigned roles remain visible for administrative diagnosis.
- Added an account-detail status indicator and integration coverage for active permission unions and inactive-account access suppression.

This does not introduce role-active flags or direct-user permission grants; neither exists in the inspected schema. Tests and browser acceptance remain pending.


### Phase 03.8 — Read-only permission diagnostics (in progress)

- Added `GET /api/v1/admin/users/{user_id}/access-check?permission_code=...` under `users:read`.
- The diagnostic checks only registered permission codes, evaluates account eligibility and assigned-role permission sources, and returns allow/deny with a safe reason and contributing role names.
- Unknown permission codes are reported as unknown/denied. The endpoint is read-only: it does not impersonate the user or execute a business action.
- Added integration coverage for granted, unknown, and account-inactive permission checks.

The endpoint does not evaluate resource-specific or branch scope because those policies are not yet implemented in the inspected RBAC model. Browser acceptance and automated execution remain pending.


### Phase 03.3 — Additional metadata regression coverage

- Added a no-op PATCH test confirming an unchanged custom-role metadata request does not commit or create an audit event.
- Added a case-insensitive duplicate-name test for metadata changes, including a pre-existing uppercase role name.
- The end-to-end API scenario already exercises create → rename/description update → duplicate → assign → verify session revocation and audit events.

**Verification remains PARTIAL / NOT VERIFIED:** tests are authored but have not been executed, and the browser workflow has not been exercised interactively.


### Current branch update — permission-change session invalidation

The RBAC permission update route now revokes every non-revoked session belonging to users assigned the changed role, in the same transaction as the permission-set update. The corresponding audit event records the revoked-session count. A focused security test was added, but it has not been executed. This remains source-level implementation evidence, not VERIFIED acceptance.
