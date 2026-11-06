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
- Profile edits support clearing optional contact/profile fields and record safe before/after values. Generic profile editing rejects password changes until the secure recovery/session-revocation workflow is implemented.
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
- The current administrator session is identified in the session list and preserved by revoke-all when an administrator operates on their own account.
- Account lifecycle transitions (activate, reactivate, deactivate, suspend) require a reason, enforce allowed state transitions, and write before/after status plus the reason to the audit log. Deactivation and suspension revoke all active sessions in the same transaction; self-deactivation and self-suspension are blocked.
- Generic profile PATCH can no longer change account status; status changes must use the reasoned lifecycle endpoint.

## Verification

- Earlier PR #15 baseline CI passed:
  - Python tests: run 42265113385.
  - Phase 01 verification: run 42265113438.
- New tests cover:
  - bounded pagination contract,
  - safe user response schema and audit snapshots,
  - separate bilingual admin directory pagination controls,
  - account creation and profile detail/edit workspaces.
- Python tests passed on commit `6c3b709d04eeca079da30e17464e8d572fca242b` (run 42271376772).
- Phase 01 verification passed on the same commit (run 42271376792).
- These results verify the automated checks for this increment; they do not verify browser/device acceptance or complete Module 02.
- No browser/device acceptance has been claimed.

## Not yet implemented — remains in Module 02 scope

1. Full user create/edit/detail forms and profile workspace with the required tabs.
2. Extend lifecycle policy with lock/unlock, expiry, deletion requests, and last active Super Admin protection.
3. Password reset/change workflow, email/phone verification, attempt limits, and rate limiting.
5. Verified external identity linking/unlinking, including Telegram proof validation and one-time linking challenges.
6. Effective-access summary integrated with Module 03, including actor authority checks and last active Super Admin protection.
7. Security events and a user activity timeline distinct from the authoritative audit log.
8. User preferences and notification preferences integrated with the existing settings/notification services.
9. Previewed, bounded bulk operations with per-record outcomes.
10. Validated CSV import/export, field-level authorization, and expiring protected downloads.
11. End-to-end API authorization, IDOR, lifecycle, concurrency, and browser acceptance coverage.
12. Full operational documentation, retention policy, and acceptance evidence.

## Database and production safety

- The increment reuses existing user, role, and audit tables and adds a reviewed Alembic migration for `user_sessions`.
- The new migration is chained after `f4a29d806c12`; it has **not** been applied to Supabase or production.
- The live database previously showed RLS disabled on public tables and broad grants that require a deliberate access-control review. Do not enable RLS blindly or revoke grants until the deployed backend connection path, service role usage, and required policies are verified.
- Future identity-link, reset-challenge, and security-event tables require reviewed Alembic migrations, isolated upgrade/downgrade tests, and documented rollback plans.
- No production deployment is part of this increment.

## Next implementation order

1. Complete and verify the new session migration and end-to-end revocation behavior in isolated test databases.
2. Implement secure recovery/verification and account lifecycle transitions, including lock/expiry policies.
3. Implement verified external identity linking.
4. Integrate effective-access display/actions with Module 03 without duplicating RBAC ownership.
5. Deliver bulk/import/export and preferences.
6. Complete security review, full E2E coverage, and browser acceptance evidence.

**Status remains `PARTIAL` until all applicable Module 02 acceptance criteria in the roadmap are implemented and verified.**
