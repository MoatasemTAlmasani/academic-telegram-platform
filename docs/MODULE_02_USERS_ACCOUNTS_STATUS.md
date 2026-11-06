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
- Profile update audit metadata records approved before/after fields and a boolean password-change indicator; it excludes password hashes, tokens, and credentials.
- Safe account response schema excludes password hashes and credentials.

## Verification

- Earlier PR #15 baseline CI passed:
  - Python tests: run 42265113385.
  - Phase 01 verification: run 42265113438.
- New tests cover:
  - bounded pagination contract,
  - safe user response schema,
  - separate bilingual admin directory pagination controls.
- Latest changes are awaiting their corresponding CI runs. Do not mark this increment verified until both Python tests and Phase 01 verification complete successfully on the latest commit.
- No browser/device acceptance has been claimed.

## Not yet implemented — remains in Module 02 scope

1. Full user create/edit/detail forms and profile workspace with the required tabs.
2. Complete account lifecycle actions and reason capture, including lock/unlock, deactivate/reactivate, expiry, and deletion requests where policy supports them.
3. Password reset/change workflow, email/phone verification, attempt limits, and rate limiting.
4. Server-side session registry, per-session revocation, revoke-all, and token invalidation on security/lifecycle events.
5. Verified external identity linking/unlinking, including Telegram proof validation and one-time linking challenges.
6. Effective-access summary integrated with Module 03, including actor authority checks and last active Super Admin protection.
7. Security events and a user activity timeline distinct from the authoritative audit log.
8. User preferences and notification preferences integrated with the existing settings/notification services.
9. Previewed, bounded bulk operations with per-record outcomes.
10. Validated CSV import/export, field-level authorization, and expiring protected downloads.
11. End-to-end API authorization, IDOR, lifecycle, concurrency, and browser acceptance coverage.
12. Full operational documentation, retention policy, and acceptance evidence.

## Database and production safety

- The current increment reuses existing user, role, and audit tables.
- No Supabase schema mutation or production migration has been applied.
- The live database previously showed RLS disabled on public tables and broad grants that require a deliberate access-control review. Do not enable RLS blindly or revoke grants until the deployed backend connection path, service role usage, and required policies are verified.
- New tables/columns, if needed for sessions, identity links, reset challenges, or security events, require a reviewed Alembic migration, isolated upgrade/downgrade tests, and a documented rollback plan.
- No production deployment is part of this increment.

## Next implementation order

1. Finish and verify the current directory/account API increment.
2. Implement account detail and editable profile workflows with safe before/after audit metadata.
3. Design and implement a real server-side session/revocation model.
4. Implement secure recovery/verification and account lifecycle transitions.
5. Implement verified external identity linking.
6. Integrate effective-access display/actions with Module 03 without duplicating RBAC ownership.
7. Deliver bulk/import/export and preferences.
8. Complete security review, full E2E coverage, and acceptance evidence.

**Status remains `PARTIAL` until all applicable Module 02 acceptance criteria in the roadmap are implemented and verified.**
