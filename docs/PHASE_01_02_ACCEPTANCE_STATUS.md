# Phase 01–02 Acceptance Verification

**Verification date:** 2026-11-07
**Branch:** `feature/admin-dashboard-enhancements`
**Base commit:** `a9547feea60752303f5306235422923c2b8c1928`
**Overall result:** `PARTIALLY VERIFIED — FINAL ACCEPTANCE STILL HAS EXPLICIT BLOCKERS`

This report records checks executed against the existing working tree. It does not authorize a merge, deployment, production database access, or migration against an application database.

## Executed checks

| Check | Result | Evidence / limitation |
|---|---|---|
| Full Python test suite | PASS | `131 passed, 1 warning in 3.97s`. The remaining warning is a Starlette deprecation warning for the legacy HTTP 422 status constant. Most tests use isolated in-memory SQLite fixtures. The PostgreSQL-only concurrency test separately connects to a local disposable database. |
| Dashboard authorization regression | PASS | Four dashboard API tests cover the `admin:access` gate, authorized empty state, suppression of request/service/quote aggregates and details without matching read permissions using seeded records, and period/service filters. Restricted metrics render as unavailable, not zero; drill-down links remain permission-gated. |
| PostgreSQL 18 concurrency | PASS (targeted scenario) | Two competing administrator deactivations serialize on the admin-role row lock: one succeeds, the other receives HTTP 409, and one active administrator remains. Test runs only against loopback PostgreSQL database `phase_acceptance`. |
| PostgreSQL timezone storage | PASS (model/schema scenario) | The targeted PostgreSQL test stores and reloads an aware UTC `User.last_seen_at` value. This test schema was created from current ORM metadata, not by applying Alembic migrations. |
| Browser smoke / authenticated Users workspace | PASS (limited scope) | Playwright Chromium authenticated against a disposable local PostgreSQL-backed app, opened the Users & Accounts workspace in RTL, and checked a 390px viewport. No page errors, API failures, or horizontal overflow were observed. Full account CRUD/lifecycle/identity/recovery workflows and LTR/accessibility/chart checks remain pending. |
| User last-seen timezone migration | PREPARED, NOT APPLIED | `User.last_seen_at` now uses `DateTime(timezone=True)`. Reversible Alembic revision `ff66aa77bb88` is the discovered migration head. Upgrade/downgrade execution against a migrated disposable PostgreSQL database remains unverified; no application database was migrated. |
| JavaScript syntax | PASS | `node --check` for admin console, Security Center, and Mini App scripts. |
| Python compilation | PASS | `compileall` for backend, model, migration, and test files. |
| Patch whitespace validation | PASS | `git diff --check`. |
| Workspace typecheck | PASS | `pnpm run build` reached and passed `tsc --build` and workspace typechecks. |
| Workspace production build | PASS WITH WARNING | `PORT=3000 BASE_PATH=/ pnpm run build` exited 0; API server bundle and Vite mockup-sandbox bundle built. Pre-build dependency verification warns `esbuild@0.28.2` build scripts are ignored and `node_modules` may be out of sync; no dependency approval or lockfile change was made. |
| ASGI / network smoke | PASS | Earlier in-process ASGI checks returned 200 for `/admin`, `/miniapp`, and all 7 referenced local JS/CSS assets. The later Playwright run also reached the local Uvicorn server successfully. |
| Production deployment | NOT RUN | No deployment, promotion, rollback, or Vercel configuration change was performed. |

## Phase 01 — Dashboard / Administration

**Status: IMPLEMENTED, PARTIALLY VERIFIED.**

Verified:
- Dashboard aggregate metrics are suppressed unless the caller has the corresponding read permission; restricted values are unavailable rather than zero.
- Request trend/status charts and service-dependent analytics are permission-gated.
- Dashboard authorization, empty-state, permission-suppression, and period/service-filter API tests pass.
- Authenticated RTL Users workspace and 390px mobile smoke check pass without page errors, API failures, or horizontal overflow.
- Workspace typecheck and production bundles build successfully with the required `PORT` and `BASE_PATH` variables.

Still required before final acceptance:
- Full browser RTL/LTR, responsive, accessibility, chart, navigation, and permission-matrix checks.
- Complete seeded dashboard aggregate tests for controlled users, requests, services, quotations, and audit records, including date-window and configured-timezone boundaries.
- Remaining chart/service/alert drill-down and recent-activity filtering/interaction checks.
- Confirm notification scope. Current delivery is in-app only; external email/SMS/Telegram delivery and durable read tracking are not implemented, and the Notification schema has no read timestamp or delivery-attempt model.
- Reconcile revenue/receivables, staff-performance, and branch-performance data gaps when authoritative ledger, assignment, and organization/branch data exist.

## Phase 02 — Users / Accounts / Security

**Status: IMPLEMENTED, PARTIALLY VERIFIED.**

Verified:
- Authentication and RBAC allow/deny checks, account creation/update/lifecycle, session scoping/revocation, audit behavior, password recovery, and isolated migration tests pass within the 131-test suite.
- Competing last-active-admin protection passes the targeted PostgreSQL 18 test.
- A PostgreSQL-only timestamp issue was discovered during browser login: `User.last_seen_at` was timezone-naive while authentication updates use aware UTC timestamps. The ORM model and a reversible migration were updated; the current metadata schema passed the targeted PostgreSQL round-trip test.

Still required before final acceptance:
- Run the new `ff66aa77bb88` migration upgrade/downgrade on a disposable PostgreSQL database that is at the prior Alembic head. Do not run it against production or any configured application database during this acceptance task.
- Exercise the full account lifecycle transaction path and session revocation under concurrent requests, beyond the targeted last-admin guard test.
- Browser/device end-to-end checks for account creation/update/deactivation/reactivation, session management, identity linking, and password recovery. Current browser run covers login and Users workspace navigation only.
- Verify production-like external identity/Telegram integration paths only when safe test credentials and a non-production destination are available. Do not involve real users or send real messages.

## Safety record

- No production database was accessed or modified.
- No Alembic migration was executed against any configured application database.
- No Supabase changes were made.
- No commit, push, merge, deployment, promotion, rollback, or Vercel configuration change was performed.
- All work remains on `feature/admin-dashboard-enhancements`; the existing working tree was preserved.


### Roadmap roles — implementation update
- The six canonical roles are now defined in code: `super_admin`, `admin`, `manager`, `staff`, `support`, and `customer`.
- Each role has an explicit least-privilege permission set; only `super_admin` receives `roles:manage`. Internal roles receive `admin:access`; customers do not.
- The role-permission update API now requires `roles:manage`; listing roles remains protected by internal admin access. The existing admin console Roles & Permissions view now uses localized role labels and disables editing without `roles:manage`.
- A reversible Alembic data migration `aa77bb88cc99` seeds the six roles, permission catalog, and baseline role-permission links. Runtime and migration permission matrices are regression-tested for exact equality.
- The migration has **not** been run against any database. No existing account was silently elevated to `super_admin`; bootstrap assignment to a specifically approved account remains pending. User-to-role assignment in account management remains a separate workflow and is not claimed complete here.
- End-to-end browser verification and a safe isolated migration upgrade/downgrade remain pending.
