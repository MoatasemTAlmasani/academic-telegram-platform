# Module 02 — Users & Accounts: Delivery Status

**Module:** 02 of Phase 1 Administration  
**Current status:** `PARTIAL`  
**Specification:** `docs/ROADMAP.md`, sections 11–32 (Module 02 detailed specification)  
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
- Phase 01 verification passed on that same UI increment (run 42287250584). The current code commit `bf7f00ef4f56229afe9efabf206a51d74b0b91e3` was verified in an isolated Vercel sandbox cloned at that exact SHA: `python -m compileall -q backend database tests` passed; `node --check` passed for `console.js` and `app.js`; the full pytest suite passed: **80 passed, 2 warnings**. The sandbox used only loopback test DATABASE_URL values; no production credentials or database were mounted, and no migration was applied. This verifies automated tests and syntax, not browser/device acceptance or a live PostgreSQL integration run.
- Phase 01 verification passed on the same commit (run 42283109349).
- The automated suite also checks JavaScript syntax with Node when Node is available in the runner.
- These results verify the automated checks for this increment; they do not verify browser/device acceptance or complete Module 02.
- No browser/device acceptance has been claimed.

## Not yet implemented — remains in Module 02 scope

1. Complete profile workspace tabs and a user activity timeline distinct from the audit log. Preference API and bilingual self-service preference UI are implemented.
2. Implement deletion-request and approved deletion/anonymization states. Account lock/expiry API enforcement and bilingual admin policy controls are implemented.
3. Password reset/recovery for accounts that cannot authenticate, email/phone verification, and recovery rate limiting.
4. Additional identity providers, broader identity-link recovery, and end-to-end verification of Telegram linking/unlinking.
5. Full effective-access integration with Module 03, including actor authority checks and role/permission administration; this increment provides a read-only role/permission summary only.
6. A unified security-event workflow and a user activity timeline distinct from the authoritative audit log; login-attempt history and throttling are implemented.
7. A separate CSV import preview/validation/commit flow; bounded bulk preview/execute APIs and the bilingual bulk-operation UI are implemented.
8. Validated CSV import, field-level authorization, and expiring protected downloads.
9. End-to-end API authorization, IDOR, lifecycle, concurrency, and browser acceptance coverage.
10. Full operational documentation, retention policy, and acceptance evidence.

## Database and production safety

- The increment reuses existing user, role, and audit tables and adds reviewed Alembic migrations for `user_sessions`, `login_attempts`, `external_identities`, `identity_link_challenges`, and user preference/account lock/expiry columns.
- The migrations are chained after `f4a29d806c12` (`aa11bb22cc33` sessions, `bb22cc33dd44` login attempts, `cc33dd44ee55` external identities/challenges); none has been applied to Supabase or production.
- The live database previously showed RLS disabled on public tables and broad grants that require a deliberate access-control review. Do not enable RLS blindly or revoke grants until the deployed backend connection path, service role usage, and required policies are verified.
- All new migration revisions still require isolated upgrade/downgrade tests against supported database engines and a documented rollback plan before deployment.
- No production deployment is part of this increment.

## Next implementation order

1. Add isolated migration upgrade/downgrade and end-to-end tests for sessions, login attempts, and external identity linking. The isolated SQLite migration upgrade/downgrade test is now implemented; production-engine and full linking-flow tests remain.
2. Implement account lock/expiry and recovery/verification workflows.
3. Integrate effective-access display/actions with Module 03 without duplicating RBAC ownership.
4. Deliver the preference and bulk-operation UI, CSV import workflow, and secure account recovery/verification through a configured delivery provider.
5. Complete security review, full E2E coverage, and browser acceptance evidence.

**Status remains `PARTIAL` until all applicable Module 02 acceptance criteria in the roadmap are implemented and verified.**
