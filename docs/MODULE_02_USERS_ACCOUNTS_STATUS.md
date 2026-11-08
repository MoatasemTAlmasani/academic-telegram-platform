# Module 02 — Users & Accounts: Delivery Status

**Module:** 02 of Phase 1 Administration
**Current status:** `PARTIAL`
**Specification:** `docs/ROADMAP.md`, sections 11–35 (Module 02 detailed specification)
**Implementation branch:** `feature/module-02-users-accounts`
**Pull request:** #15

This document records implementation evidence. The approved roadmap remains the source of target scope. A screen, route, or passing smoke test does not make the module complete.

## Implemented in the current increment

- Existing administration navigation uses the approved bilingual label: **User & Account Management / إدارة المستخدمين والحسابات**.
- Existing user directory API supports search, status/role filters, bounded server-side pagination, and a safe response model.
- User and customer directory pages now use independent server-side pagination controls.
- The admin workspace includes a bilingual, validated account-creation form; it submits through the existing protected API and creates a customer account without accepting a privileged role from the browser.
- The admin workspace includes a user detail panel and profile edit form; profile reads/updates use existing protected APIs, and the edit form is hidden without the update permission.
- Profile edits support clearing optional contact/profile fields and record safe before/after values. Generic profile editing rejects password changes; a separate current-password-verified workflow handles password changes and session revocation.
- Usernames are trimmed and compared case-insensitively during account creation/update; email addresses are normalized to lowercase and conflict-checked case-insensitively.
- Unsupported account status filters and mutations are rejected.
- Archived users are excluded from directory/detail retrieval.
- Account archival uses the existing `deleted_at` marker and retains business references instead of hard-deleting the user.
- Login and protected API requests reject inactive, suspended, or soft-deleted accounts.
- Module 02 account creation/update cannot assign arbitrary roles. Role catalog and privileged role governance remain in Module 03; this prevents a generic user-management endpoint from becoming a privilege-escalation path.
- Account creation and its audit record are committed together.
- Profile update audit metadata records approved before/after fields and excludes password hashes, tokens, and credentials.
- Safe account response schema excludes password hashes and credentials.
- Login creates a persistent server-side session before issuing a session-bound JWT. Protected requests reject missing, expired, or revoked session records.
- Administrators can inspect the latest 100 sessions, revoke one session, or revoke all active sessions. Revocations are audited; account deactivation/suspension and archival revoke sessions in the same transaction.
- Administrators can preview and execute bounded bulk lifecycle actions (up to 100 accounts) with per-record outcomes, reasoned audit records, self-protection, and last-active-admin safeguards. The bilingual admin workspace now supports selecting accounts across directory pages, reviewing a server-generated preview, confirming execution, and viewing per-account outcomes. Preview eligibility also checks self-protection and last-active-admin safeguards. A credential-free CSV directory export is available with a 5,000-row cap and a workspace export control.
- Administrators can inspect verified external identities linked to an account; the view excludes challenge tokens and is read-only. Self-service Telegram linking uses a short-lived, single-use challenge in the authentication API.
- Administrators can inspect the latest 50 account-linked login attempts with timestamp, outcome, and IP address; the endpoint never exposes username hashes or credentials.
- The account workspace includes a separate chronological activity timeline that merges account-targeted audit events and login outcomes. Its paginated API requires both `users:read` and `audit:read`, uses database-side ordering/limits, and omits IP addresses, raw metadata, and secrets. The timeline now supports server-side source and exact event filters, plus a permission-gated CSV export capped at 5,000 rows; the export excludes IP addresses, raw metadata, and credentials.
- The user profile workspace now has nine bilingual tabs: Overview, Personal Information, Account & Status, Roles & Access, Sessions, Linked Identities, Security, Activity, and Audit History. Existing forms, data loaders, and APIs are reused; tab switching preserves permission/ownership-based hidden states, and keyboard navigation supports arrow keys, Home, and End.
- Public sign-in now includes a bilingual password-recovery flow. The API sends an eight-digit, ten-minute, single-use code only to a pre-verified Telegram identity already linked to an active account; requests use a generic response to avoid account enumeration. Codes are HMAC-hashed, limited to five verification attempts, and request volume is throttled by HMAC-keyed identifier and IP hashes. Successful recovery audits the event and revokes all active sessions.
- Users with `audit:read` can inspect the latest 100 redacted audit events related to the account or performed by it. The endpoint deliberately omits arbitrary metadata, tokens, and credential fields.
- The account detail workspace includes a read-only effective-access summary of assigned roles and permission codes, loaded from the existing RBAC relations. It does not mutate role assignments or permissions; Module 03 remains the owner of those workflows.
- The current administrator session is identified in the session list and preserved by revoke-all when an administrator operates on their own account.
- Account lifecycle transitions (activate, reactivate, deactivate, suspend) require a reason, enforce allowed state transitions, and write before/after status plus the reason to the audit log. Deactivation and suspension revoke all active sessions in the same transaction; self-deactivation and self-suspension are blocked.
- Deactivation, suspension, and archival protect the last active account assigned the existing `admin` role. The guard locks the admin role row before counting active administrators to serialize concurrent transitions on databases supporting row locks.
- Generic profile PATCH can no longer change account status; status changes must use the reasoned lifecycle endpoint.
- Account archival requires a meaningful reason, records it in the audit log, preserves linked business records, and revokes all sessions. The UI exposes the archive action only with the delete permission.
- Authenticated users can read/update allowlisted personal preferences (language, timezone, theme, date format, email/Telegram notification preferences); preference changes are audited without recording values. The bilingual account workspace exposes the preference form.
- Accounts support temporary lock and expiry timestamps; login and authenticated API access reject locked or expired accounts, and administrators can set policy with a reason, audit snapshot, last-admin protection, and session revocation on lock. The bilingual account workspace exposes these controls.
- Authenticated users can change their own password only after supplying the current password; new passwords require at least 12 characters, password changes are audited without credential data, and all active sessions are revoked to require reauthentication.
- Login attempts are stored using a keyed HMAC-SHA256 username key rather than raw usernames. Database-backed rolling-window throttling rejects further attempts after 5 failures for a username/IP pair or 10 for a username across IPs within 15 minutes; failed and successful attempts are recorded.
- Telegram identity linking uses a short-lived, single-use challenge: an authenticated account requests a code, then sends `/link CODE` to the official bot. The bot validates the Telegram sender from the Bot API update, stores a verified external identity, and records an audit event. Raw challenge codes are not stored; only SHA-256 hashes are persisted.
- Telegram identity unlinking is available only when the account has a password-based sign-in method. Existing Telegram-linked users are not automatically merged; conflicting legacy identities are rejected.

## Verification

- Earlier PR #15 baseline CI passed:
  - Python tests: run 42265113385.
  - Phase 01 verification: run 42265113438.
- New tests cover:
  - bounded pagination and credential-free response contracts,
  - safe audit snapshots,
  - bilingual user/customer directories, account creation, profile editing, session controls, lifecycle/archive forms, linked-identity, login-history, permission-gated audit-history, and effective-access panels,
  - persistent session creation, session-bound JWTs, lifecycle API contracts, password-change validation, last-active-admin protection (including inactive-admin behavior), and isolated migration upgrade/downgrade behavior.
- Python tests passed on commit `6c3b709d04eeca079da30e17464e8d572fca242b` (run 42271376772).
- Phase 01 verification passed on the same commit (run 42271376792).
- Python tests passed on commit `5c03071a3e9e906841ceb02e424f298511999021` (run 42281708050).
- Phase 01 verification passed on the same commit (run 42281707996).
- Python tests passed on commit `d9bdddeace4f1a43542a3a181a8685396573a75e` (run 42282611667), including the isolated SQLite upgrade/downgrade test for all three Module 02 migration revisions.
- Phase 01 verification passed on the same commit (run 42282611644).
- Python tests passed on current functional commit `e6ba5191ff7881c7309cfe9b715d51de006695b8` (run 42283109343): **73 passed, 2 warnings**.
- Bulk-operation UI increment passed Python tests on commit `4b02e24923016edb2d8a78dd9503bf12716d9180` (run 42287250581): **79 passed, 2 warnings**.
- Phase 01 verification passed on that same UI increment (run 42287250584). Code commit `082e9cf8c346fd490ab7e31d255a005878f7d405` was checked in an isolated Vercel sandbox cloned at that exact SHA: Python compileall passed; Node syntax check for `console.js` passed; full pytest suite: **82 passed, 2 warnings**. An additional isolated SQLite integration check exercised the timeline query and verified mixed-source ordering and offset pagination. The sandbox used loopback-only test DATABASE_URL values; no production credentials or database were mounted, and no migration was applied.
- The activity filter/export increment passed isolated SQLite query and CSV tests as part of **83 passing tests, 2 warnings** on code commit `da66210004ce3564992a85cfc8b94f3c2cadcb91`; Node syntax check for `console.js` passed. Workspace TypeScript typecheck and full package build also passed on that exact code commit in the isolated Vercel sandbox (`PORT=8081`, `BASE_PATH=/__mockup`).
- GitHub Actions on the latest PR head `be79551cc0044d4236b06b3091485e5ab9645f0e`: Python tests passed (run 42290144636) and Phase 01 verification passed (run 42290144567).
- These checks verify automated tests, query behavior on SQLite, and syntax. They do not establish browser/device acceptance or a live PostgreSQL integration run.
- The profile-tab increment passed the full isolated test suite on the sandbox working tree: **84 passed, 2 warnings**; `node --check backend/app/static/admin/console.js` and `git diff --check` passed. The test database URL pointed to a non-routable local test target; no live PostgreSQL connection, production database, migration, or deployment was used. `PORT=8081 BASE_PATH=/__mockup pnpm run build` also passed. CI for the resulting PR commit and browser/device acceptance are still pending.
- The recovery/API/UI increment passed **68 targeted tests, 2 warnings** across recovery, migration, and admin-console suites. The recovery tests cover successful delivery to a verified Telegram identity, password update/session revocation, unlinked identities, provider failure, invalid-code attempt exhaustion, generic unknown-account responses, and request throttling. The new migration was exercised with isolated SQLite upgrade/downgrade operations. `node --check` passed for `login.js` and `console.js`; `git diff --check` passed. No live database or Telegram API was contacted.
- The full isolated Python suite passed: **93 passed, 2 warnings**. `PORT=8081 BASE_PATH=/__mockup pnpm run build` passed, including workspace typecheck and frontend builds. The only warnings are the pre-existing short test JWT key warnings.
- Phase 01 verification passed on the same commit (run 42283109349).
- The automated suite also checks JavaScript syntax with Node when Node is available in the runner.
- These results verify the automated checks for this increment; they do not verify browser/device acceptance or complete Module 02.
- No browser/device acceptance has been claimed.

## Not yet implemented — remains in Module 02 scope

1. Email and phone ownership verification, and password recovery through email/SMS. No email/SMS delivery provider is configured in the current repository; the implemented recovery channel is verified Telegram only.
2. Additional identity providers, broader identity-link recovery, and full browser/E2E verification of Telegram linking/unlinking and password recovery.
3. Implement deletion-request and approved deletion/anonymization states. Account lock/expiry API enforcement and bilingual admin policy controls are implemented.
4. Full effective-access integration with Module 03, including actor authority checks and role/permission administration; the current workspace provides a read-only role/permission summary only.
5. A unified security-event triage workflow integrated with Module 22. Account activity timeline, login-attempt history, and throttling are implemented.
6. A separate CSV import preview/validation/commit flow; bounded bulk preview/execute APIs and the bilingual bulk-operation UI are implemented.
7. Validated CSV import, field-level authorization, and expiring protected downloads.
8. Complete API authorization/IDOR, production-engine concurrency, and browser acceptance coverage. Initial isolated API integration coverage now exists for RBAC denial, safe directory responses, cross-account session revocation, lifecycle session revocation/auditing, and missing-account behavior.
9. Full operational documentation, retention policy, and acceptance evidence.

## Database and production safety

- The increment reuses existing user, role, and audit tables and adds Alembic migrations for `user_sessions`, `login_attempts`, `external_identities`, `identity_link_challenges`, user preference/account lock/expiry columns, and password recovery challenge/request-throttle tables.
- The migrations are chained after `f4a29d806c12`: `aa11bb22cc33` sessions, `bb22cc33dd44` login attempts, `cc33dd44ee55` external identities/challenges, `dd44ee55ff66` preferences/account controls, and `ee55ff66aa77` password recovery challenges and throttling. None has been applied to Supabase or production.
- The live database previously showed RLS disabled on public tables and broad grants that require a deliberate access-control review. Do not enable RLS blindly or revoke grants until the deployed backend connection path, service role usage, and required policies are verified.
- All new migration revisions still require isolated upgrade/downgrade tests against supported database engines and a documented rollback plan before deployment.
- No production deployment is part of this increment.

## Next implementation order

1. Add a real email delivery adapter only after selecting and configuring a provider (SMTP/Resend/SendGrid) and its verified sender domain; add phone verification only after an SMS provider is selected and configured. Do not expose recovery codes or claim delivery without provider confirmation.
2. Add contact-ownership verification challenges and integrate provider delivery attempts with Module 14 notification delivery tracking.
3. Deliver CSV import preview/validation/commit only after the secure invitation or password-setup path is established; never create accounts with unknown or unusable credentials.
4. Define the approved retention/deletion policy before implementing deletion requests or anonymization; integrate effective-access governance with Module 03 and security-event triage with Module 22.
5. Complete IDOR/concurrency/API authorization coverage, production-engine migration tests, full browser/E2E scenarios, operational documentation, and acceptance evidence.

**Status remains `PARTIAL` until all applicable Module 02 acceptance criteria in the roadmap are implemented and verified.**


## Latest security verification — 2026-11-07

- Added `tests/test_admin_users_api_integration.py` with five HTTP-level integration scenarios against the actual FastAPI application and an isolated async SQLite database: directory listing/safe response, missing-permission denial, cross-account session-revocation IDOR denial, lifecycle deactivation with session revocation and audit persistence, and missing-account handling.
- Added `tests/test_admin_users_security.py` with seven focused checks covering the authorization dependency on every admin-user route, exact RBAC allow/deny behavior, cross-user session-revocation scoping, bulk session-revocation scoping to active/unexpired sessions, the last-active-admin role-row lock, and row-lock presence on sensitive lifecycle/access-policy mutations.
- The new API integration file passed: **5 passed**; the focused security file passed: **7 passed**.
- Full isolated Python test suite after this increment: **105 passed, 2 warnings**.
- The tests used a non-routable placeholder PostgreSQL URL only to initialize application imports; no database connection was opened and no live database was accessed.
- These checks validate route behavior, RBAC enforcement, SQL query scoping, audit/session persistence, and lock clauses on isolated SQLite. They are not a live PostgreSQL concurrency/transaction integration test and do not replace browser/E2E authorization acceptance.
- Current working tree remains uncommitted and unpushed. PR #15 remains open and unmerged; no deployment or production migration was performed.

## Extended account lifecycle and privilege verification — 2026-11-07

- Extended `tests/test_admin_users_api_integration.py` from five to **eleven HTTP-level scenarios** using the actual FastAPI application and an isolated in-memory SQLite database.
- Added coverage for successful account creation, safe response fields, password hashing, and `user.created` audit persistence; duplicate identifiers and invalid payload rejection; prevention of privileged-role assignment during creation and update; profile update before/after audit metadata without secrets; lifecycle deactivation and reactivation; session revocation scoped to the target account; archive soft-delete and `user.archived` audit persistence; and last-active-administrator protection through both lifecycle and archive HTTP endpoints.
- Focused API integration result: **11 passed, 1 warning**. Full isolated Python suite: **111 passed, 3 warnings**.
- PostgreSQL concurrency verification remains **NOT RUN**. The sandbox does not provide `pg_isready`, a PostgreSQL server binary, or Docker; SQLite results are not represented as PostgreSQL row-lock or concurrency evidence.
- Remaining acceptance gaps include a real isolated PostgreSQL integration/concurrency run, browser/device E2E acceptance, CI verification on the PR commit, and the outstanding Module 02 roadmap requirements listed above.
- No production Supabase connection, live database access, migration application, real Telegram API call, commit, push, merge, or deployment occurred.

**Module 02 remains `PARTIAL`.**

## Repository status reconciliation — 2026-11-08

This section supersedes older statements above that describe the repository as uncommitted/unpushed or PR #15 as the current open delivery. Those statements are historical evidence from earlier checkpoints, not the current GitHub state.

- The approved User & Account Management dashboard navigation work was delivered in **PR #19**, merged to `main` (merge commit `6862f220a196b327852786de4c1f6218f7ce771e`).
- The profile-panel HTML markup correction and regression test were delivered in **PR #20**, merged to `main` (merge commit `f0c80bef27b2d7f3367af90ecc93c002fed1aa65`).
- PR #20's Python test workflow and Phase 01 verification workflow both completed successfully; its Vercel commit status was successful. This is CI evidence for the profile markup fix, not browser/device acceptance.
- The repository's default branch is `main`. The Module 02 product status remains **PARTIAL**; merging these UI/navigation fixes does not close the outstanding Module 02 requirements.
- No production database migration or production database mutation was performed as part of PR #20. No live PostgreSQL concurrency test or browser/device acceptance is claimed here.

### Next safe delivery priorities

1. Keep email/SMS verification and recovery blocked until a provider, verified sender/phone, secret configuration, and delivery-failure contract are explicitly selected. Telegram remains the implemented recovery channel; do not create a fake delivery adapter.
2. Define a reviewed retention, deletion-request, and anonymization policy before implementing destructive or irreversible account states.
3. Implement CSV import only after a secure invitation/password-setup workflow exists; require preview, row-level validation, field-level authorization, bounded commit, idempotency, and auditable per-row outcomes.
4. Coordinate effective-access administration with Module 03 and security-event triage with Module 22 rather than duplicating their ownership in Module 02.
5. Close the remaining evidence gaps: isolated PostgreSQL migration/concurrency tests, API authorization/IDOR coverage, browser/E2E flows, and operational documentation. SQLite-only checks must not be reported as PostgreSQL concurrency proof.

**Current acceptance decision: Module 02 remains `PARTIAL`; do not mark it `VERIFIED` until the roadmap's end-to-end acceptance contract and all applicable outstanding requirements have evidence.**

## Security and PostgreSQL verification update — 2026-11-08

- **PR #22** merged to `main` as `5799a7471de22d4ecc3c5c609dbd2d17838b2e51`: account-directory and account-activity CSV exports now prefix spreadsheet-formula-leading untrusted text with a text marker. HTTP-level regression coverage verifies formula payloads in profile fields, phone values, and audit descriptions.
- PR #22 CI: **162 passed, 1 skipped, 2 warnings** in the Python workflow. The skipped test was the dedicated PostgreSQL concurrency acceptance test because that workflow does not provide its database. Phase 01 verification also passed. Vercel production deployment for the merged commit reached `READY`; a query of production error/fatal runtime logs for the observed 10-minute window returned no entries.
- **PR #23** merged to `main` as `a0681b0410532f0a643ad17c91b1b602726e2b71`: Phase 01 CI now creates a separate disposable PostgreSQL database named `phase_acceptance` and supplies `PHASE_ACCEPTANCE_DATABASE_URL`. The pre-existing PostgreSQL concurrency test's strict localhost/database-name guard remains in place; the general `ehteraf_test` database is not used for destructive schema setup.
- PR #23 Phase 01 verification passed: **163 passed, 2 warnings**, with no skipped tests. This run includes the dedicated PostgreSQL concurrency acceptance scenario. The separate Python workflow passed as well (its configuration does not provide the dedicated PostgreSQL database, so that workflow alone is not evidence of PostgreSQL concurrency).
- Vercel production deployment for PR #23's merge commit reached `READY`; the observed 10-minute production error/fatal runtime-log query returned no entries.
- These CI checks use only the ephemeral PostgreSQL service in GitHub Actions. They do not imply that a production database was accessed or migrated.

**Remaining Module 02 status: `PARTIAL`.** The email/SMS provider and verified sender, deletion/retention policy, secure CSV import flow, cross-module governance integration, browser/device E2E acceptance, and broader production-engine/API authorization evidence remain outstanding.

## Exact API permission matrix acceptance — 2026-11-08

- **PR #25** merged to `main` as `94bf2d03da2036a6227566a7411d0a7f7c871304`.
- Added a route-by-route method/path permission matrix for all **21** Module 02 admin-user API routes. The regression test asserts the exact least-privilege permission set for each route, including the requirement that activity and activity CSV endpoints require both `users:read` and `audit:read`.
- Existing route authentication-presence checks and cross-account session revocation scoping checks remain in place.
- Python workflow: **163 passed, 1 skipped, 2 warnings**; the skipped case is the PostgreSQL concurrency test because this workflow does not provision its dedicated database.
- Phase 01 verification: **164 passed, 2 warnings**, with the dedicated disposable PostgreSQL concurrency database enabled and no skipped tests.
- Vercel production deployment for the merge commit reached `READY`; the observed 10-minute error/fatal runtime-log query returned no entries.
- The first draft of the new matrix test exposed a test-harness assumption about callable dependencies (`HTTPBearer` is callable but has no `__name__`). The test was corrected to inspect dependency names safely; the corrected commit passed both workflows before merge.

**Module 02 remains `PARTIAL`.** The permission matrix strengthens regression evidence but does not replace browser/E2E acceptance or close the remaining provider, retention/deletion, secure-import, and cross-module governance requirements.
