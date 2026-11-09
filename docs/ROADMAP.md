# EHTERAF Platform Roadmap

**Status:** Approved delivery roadmap  
**Architecture baseline:** `docs/EHTERAF_MASTER_REFERENCE.md`  
**Administration delivery contract:** `docs/ADMIN_SYSTEM_DELIVERY_BLUEPRINT.md`  
**Platform architecture:** `docs/EHTERAF_PLATFORM_ARCHITECTURE.md`

This roadmap adopts the approved **five-system architecture** and the **23-module Administration structure** as the authoritative plan. The former roadmap sequence that placed Core Persistence in Phase 2 and Authentication & Administration in Phase 3 is superseded by this document. Persistence, authentication, authorization, audit, localization, and testing are foundational requirements delivered with the modules that depend on them; they are not reasons to postpone the approved Administration workstream.

## 1. Product structure — five integrated systems

1. **Super Admin & Administration Dashboard** — platform governance, configuration, operations, and reporting.
2. **Telegram Mini App** — customer-facing service discovery and request workspace inside Telegram.
3. **Telegram Bot** — conversations, service discovery, request assistance, support, notifications, and routing.
4. **Customer Portal** — customer account and service workspace on the web.
5. **Official Public Website** — company profile, public service catalog, content, SEO, and contact.

These are five experiences backed by shared identity, authorization, APIs, and business data—not five independent systems or customer databases. A customer must retain one identity across web and Telegram channels.

## 2. Approved technical and product constraints

- Continue the existing FastAPI modular monolith and current frontend architecture.
- Preserve existing routes, APIs, integrations, and user data unless a reviewed change explicitly authorizes otherwise.
- Arabic and English are first-class across all five systems, including complete RTL/LTR behavior.
- Support responsive desktop, laptop, tablet, and mobile layouts; light and dark themes.
- Use one central identity and verified channel linking; do not create duplicate customers when a customer changes channel.
- No Firebase.
- Do not introduce a new service, database, framework, or foundational technology without a reviewed ADR and approval.
- Do not fabricate customers, requests, testimonials, revenue, financial balances, delivery status, or operational health.
- Enforce permissions on the backend. Hiding a button or navigation item is not authorization.
- Keep secrets in environment/secret storage; never expose tokens, password hashes, or sensitive payloads.
- Schema changes require reviewed, reversible Alembic migrations and isolated-database tests. Never run development migrations against production.
- Financial reporting requires authoritative invoice/payment/ledger records.
- AI-generated suggestions must be labeled and consequential external actions require human approval.

## 3. Phase 0 — Existing project foundation

**Goal:** maintain and strengthen the existing application foundation.

Scope:
- Existing Python/FastAPI application and modular domain boundaries.
- Environment configuration, logging, and error handling.
- Health/readiness endpoint foundations.
- API versioning and application-service boundaries.
- Existing database and migration infrastructure.
- Telegram destination and publishing-job contracts.
- CI, tests, security, and architecture documentation.

**Status:** Existing foundation. This is not a request to rebuild or reset the project.

## 4. Phase 1 — Super Admin & Administration Dashboard (23 modules)

**Goal:** deliver the complete central administration system. This is the approved first delivery workstream and remains active until all 23 modules meet their acceptance criteria.

### Group A — Foundation and control

#### 01. Super Admin executive dashboard
- Authorization-aware dashboard and operational overview.
- Real KPIs from persisted records, reporting periods, service/status filters, charts, recent activity, and actionable queues.
- Drill-down from every metric to authorized source records.
- Revenue, receivables, staff performance, branch performance, and integration health remain unavailable until authoritative source data exists.

#### 02. Users and accounts
- Search, filter, paginate, view, create, update, suspend, reactivate, and safely manage platform accounts.
- Manage linked identities/channels and revoke sessions where supported.
- Prevent duplicate identities, self-privilege escalation, and secret exposure.

#### 03. Roles and permissions (RBAC)
- Manage roles, permission catalog, role-permission assignments, and user-role assignments.
- Enforce least privilege on every protected API.
- Separate permission to administer RBAC from permission to access the admin console.
- Protect the last active Super Admin and audit privileged changes.


**Detailed scope — Roles & Permissions administration**

**Administration dashboard navigation**
- Add one primary sidebar section named **Roles & Permissions** (Arabic: **إدارة الأدوار والصلاحيات**) inside the existing administration dashboard. Keep all related screens nested beneath this section; do not create a separate application or disconnected navigation area.
- Provide these permission-filtered child pages: Overview; Roles; Permission Catalog; Role Permission Matrix; User Role Assignments; Effective User Access; RBAC Change History; Security & Protection Policies.
- Preserve the existing authenticated shell, breadcrumbs, responsive sidebar, theme, language, and RTL/LTR behavior. Direct URL access must be protected by backend authorization even when a navigation item is hidden.

**1. RBAC overview**
- Show database-backed counts for total, active, inactive, and system roles; permission catalog size; users with assigned roles; and recent RBAC changes.
- Provide links to the corresponding filtered lists and recent events.
- Show only verifiable persisted data. Do not fabricate KPIs or treat missing data as zero without an explicit definition.
- Apply the relevant read permissions to each metric and drill-down.

**2. Roles directory and lifecycle**
- List roles with localized name/description, immutable role code, system/custom classification, active status, permission count, assigned-user count, and last update.
- Support server-side search, filtering, sorting, pagination, and role detail views.
- Authorized operators may create, edit, activate, deactivate, and duplicate custom roles, subject to privilege boundaries.
- Validate required localized names, unique normalized role codes, reserved/system codes, field lengths, and valid status transitions.
- A newly created role receives no implicit permissions. Duplicating a role copies only explicitly permitted assignments and never copies protected identity or Super Admin status.
- Before deactivation, show the number of affected users and explain the effective-access impact. Deactivation must not delete historical relationships or audit evidence.
- Protect system roles and the last active Super Admin from deletion, deactivation, or privilege reduction. Any exceptional protected-role workflow must be explicit, separately authorized, audited, and covered by security tests.

**3. Permission Catalog**
- Maintain one authoritative catalog of permissions used by backend authorization and administration UI.
- Group entries by the actual registered platform modules and resources; do not invent permissions for modules or actions that do not exist.
- For each permission expose its stable code, Arabic and English labels, description, module/resource, action, sensitivity/administrative classification, active/deprecated state, and roles currently assigned where authorized.
- Support search by code/name, module and action filters, sensitive-permission filters, and unassigned-permission views.
- Use a consistent documented naming convention such as `module:resource:action`, while preserving existing permission codes and compatibility. Any code migration requires an explicit mapping, backward-compatibility plan, and tests.
- Unknown permission codes must be rejected. Retire/deprecate permissions safely; do not silently delete permissions still referenced by roles or code.

**4. Role Permission Matrix**
- Allow an authorized operator to select a role and inspect its complete current permission set grouped by module/resource.
- Support granting and revoking individual permissions and clearly scoped group selections. Group selection must show the exact permissions affected before saving; it must not imply blanket access beyond the displayed set.
- Display sensitive permissions distinctly, explain their impact, and require confirmation where policy classifies the change as high risk.
- Show an explicit before/after change preview, unsaved-change state, validation errors, and conflict handling for concurrent edits.
- Save the complete validated change atomically. If any permission is unknown, unauthorized, or invalid, reject the entire operation without partial updates.
- Enforce the grantor's authority: an operator cannot grant permissions they are not authorized to administer or exceed their own permitted privilege boundary. Protect system/Super Admin role assignments.

**5. User Role Assignments**
- Search and inspect users using only fields the operator is authorized to see; show account status and current active/inactive roles.
- Assign or remove roles through an explicit review-and-confirm workflow that previews the resulting effective-access changes.
- Reject assignment of inactive roles and enforce account eligibility, organization/branch constraints where those policies are implemented, and the operator's grant authority.
- Prevent self-escalation and indirect escalation through role or permission changes. Protect the last active Super Admin from removal, suspension, or privilege reduction.
- Record the actor, target user, role, operation, timestamp, reason when required, and safe before/after metadata.
- Preserve assignment history where supported by the existing data/audit model; do not invent validity periods or direct-user grants unless explicitly designed and approved.

**6. Effective User Access**
- Provide an authorized, server-calculated view of a user's effective permissions, based on active assigned roles and the platform's actual authorization rules.
- Show which role(s) contribute each permission, relevant account/role status, and applicable organization/branch scope restrictions where implemented.
- If the platform supports explicit deny rules or direct user grants, document and apply their precedence. Otherwise do not introduce an assumed deny/allow hierarchy or unsupported direct grants.
- Provide a diagnostic access-check for a selected user, permission, and resource/scope where applicable. Return allow/deny and a safe reason/source explanation without exposing secrets or bypassing normal API authorization.
- Keep this diagnostic read-only. It must not impersonate users or execute the requested business action.

**7. RBAC change history**
- Provide searchable, server-paginated history for role creation/update/status changes, permission grants/revocations, user-role assignments/removals, protected-role attempts, and denied privileged operations where safely recordable.
- Record actor, target/resource, action, timestamp, outcome, request/correlation ID, reason when supplied, and sanitized before/after values.
- Reuse the existing AuditLog/audit service and established transaction/outbox pattern. Do not create a parallel audit subsystem.
- Never log passwords, access/refresh tokens, secrets, full private documents, or unnecessary personal data.
- Restrict history viewing and export with separate permissions. Audit records must not be editable through ordinary RBAC screens.

**8. Security and protection policies**
- Keep permission to administer RBAC distinct from permission to enter the admin console. A broad admin-console permission must not implicitly authorize role/permission mutations.
- Enforce authorization on every protected backend endpoint; frontend navigation and button visibility are usability controls only.
- Prevent privilege escalation, self-escalation, assignment of permissions beyond the operator's authority, insecure object references (IDOR), and cross-scope access.
- Protect the last active Super Admin using a transaction-safe invariant that remains correct under concurrent requests. Do not rely only on role names or frontend checks to identify the protected principal.
- Re-evaluate authorization after role/permission changes. Invalidate or refresh relevant permission caches/sessions/tokens according to the existing authentication design so revoked permissions do not remain effective through stale claims.
- Treat organization/branch scoping as backend policy constraints. Do not implement scope enforcement as UI filters or introduce speculative multi-tenancy in this stage.
- Use least privilege, safe error responses, and security event auditing.

**Data model and API constraints**
- Existing `Role`, `Permission`, `user_roles`, and `role_permissions` records remain authoritative. Inspect their actual fields, constraints, relationships, seed data, and usage before changing anything.
- Reuse existing RBAC routes, authorization dependencies, services, schemas, and audit infrastructure. Extend them only where a demonstrated gap exists; do not add duplicate endpoints or parallel models.
- Any proposed endpoint must follow the repository's existing API versioning and response conventions. Expected capabilities include role list/detail/create/update/status, permission catalog, role-permission read/update, user-role read/update, effective-access inspection, access diagnostics, and audit search/export; reconcile these with existing routes before implementation.
- All mutations require backend permission checks, input validation, transactional persistence, concurrency-safe invariants, and audit records.
- Add database schema only when essential and justified. Any schema change requires a reviewed reversible migration and isolated-database tests; never run migrations against production as part of this delivery.

**Localization, accessibility, and UI states**
- Arabic and English labels, descriptions, validation messages, confirmations, and errors must be complete; verify true RTL/LTR layouts.
- Support desktop, tablet, and mobile layouts, keyboard navigation, visible focus, and the existing light/dark theme.
- Every screen must implement loading, empty, error, success, validation, permission-denied, conflict, and confirmation states as applicable.
- Tables and search/filter/pagination must use server-side contracts for large datasets. Avoid loading the full user or permission catalog into the browser unnecessarily.

**Required verification and security tests**
- Test anonymous, authenticated-but-unauthorized, and authorized requests for every protected operation.
- Test role create/update/duplicate/activate/deactivate, unique and reserved codes, inactive-role assignment, and protected system roles.
- Test permission catalog integrity, unknown permission rejection, unauthorized grant/revoke, atomic rollback, and concurrent matrix updates.
- Test user-role assignment/removal, multiple-role effective permission union under the actual policy, self-escalation, indirect escalation, and cross-scope access.
- Test last active Super Admin lockout under sequential and concurrent operations.
- Test stale token/session/cache behavior immediately after permission revocation and grant.
- Test effective-access and diagnostic results against actual backend authorization decisions; UI and API must agree.
- Test audit completeness, safe before/after metadata, denied privileged attempts, pagination, and export authorization.
- Test the complete UI flows in Arabic/English, RTL/LTR, responsive viewports, and all relevant UI states.
- Run tests only against isolated test databases and non-production identities. Record commands, results, CI run references, screenshots or browser evidence where available, and known limitations.

**Definition of done**
- All eight dashboard pages/workflows above are connected to real persisted data and existing application services.
- No protected action depends solely on frontend visibility.
- Permission administration is separated from general admin-console access.
- Super Admin protection, least privilege, stale-authorization handling, and audit behavior are proven by automated tests.
- Existing routes, roles, permission codes, user data, and integrations remain compatible or have a documented reviewed migration path.
- Documentation, permission matrix, changed-file list, test evidence, known limitations, and rollback notes are recorded.
- Set status to `VERIFIED` only after implementation and acceptance evidence pass; otherwise report the accurate status (`NOT_STARTED`, `IN_PROGRESS`, `PARTIAL`, `IMPLEMENTED`, or `BLOCKED`).

**Implementation sequence**
1. Inventory existing roles, permission codes, tables, relationships, APIs, dependencies, frontend navigation/pages, audit events, tests, and current gaps without changing behavior.
2. Establish and test dedicated RBAC-administration authorization and a safe bootstrap path before enabling privileged editing.
3. Complete role directory and lifecycle.
4. Complete permission catalog and role-permission matrix.
5. Complete user-role assignment and protection invariants.
6. Complete effective-access diagnostics and stale-authorization handling.
7. Complete audit history, dashboard integration, localization, and responsive behavior.
8. Run security/integration/UI acceptance tests, document evidence, and update the stage status.

#### 04. Platform-wide settings
- Manage platform identity, branding, locale, timezone, date/number/currency formats, supported policies, notification settings, integrations, and operational preferences.
- Validate settings, preserve omitted values during partial updates, protect secrets, and audit changes.

#### 05. Organizations and branches
- Manage organizations and branches, their profiles, status, and authorized membership/scope.
- Define data ownership and isolation rules before implementing organization/branch scoping.
- Hybrid readiness does not authorize premature full multi-tenancy; document the model through an ADR.

### Group B — Customers, services, and requests

#### 06. Service catalog management
- Full service and category lifecycle, bilingual content, descriptions, media, pricing/quote policy, required customer fields, visibility, ordering, and preview.
- Keep the admin catalog consistent with the public website, portal, and Telegram experiences.

#### 07. Customer management and identity linking
- Customer profiles, contact details, search, filtering, status, and related activity.
- One customer identity across the portal and Telegram Mini App/Bot through verified account linking.
- Prevent duplicates and protect personal data.

#### 08. Request management
- Full request lifecycle, filtering, detail view, permitted updates/cancellation, priorities, due dates, notes, assignment, and status transitions.
- Maintain request history and connect customer notifications through delivery-aware services.

#### 09. Files and document management
- Upload, classify, preview, download, version, archive, and manage files attached to customers and requests.
- Validate file type/size/content, enforce ownership and access permissions, and apply retention rules.

#### 10. Quotations management
- Create, revise, approve, send, accept, reject, expire, and cancel quotations.
- Support currency, line items, discounts/taxes where approved, document rendering, and immutable revision/history records.
- Keep quotation state distinct from invoice/payment state.

### Group C — Operations and finance

#### 11. Financial management, invoices, payments, and receivables
- Invoice issuance, payment recording, partial payments, allocation, refunds, adjustments, due dates, overdue balances, and customer statements.
- Design and verify an auditable ledger before showing financial KPIs.
- Use decimal money types, explicit currency, idempotency, immutable posted entries, and compensating reversals.

#### 12. Staff management
- Staff profiles, specialties, skills, availability, active status, and authorized operational details.
- Link staff profiles to platform identities and use actual assignments as the source for workload metrics.

#### 13. Tasks and workflow management
- Create tasks from requests or independently; assign owners, priorities, due dates, checklists, dependencies, comments, blockers, and completion evidence.
- Enforce valid state transitions, scope, history, and timezone-aware escalation.

#### 14. Communication and notifications
- In-app notification center, read/unread state, filtering, preferences, and bilingual templates.
- Track queued, sent, delivered, failed, and retried states only when supported by provider evidence.
- Separate notification creation from delivery attempts; implement deduplication and bounded retry.

#### 15. Telegram bots, channels, groups, and destinations
- Manage bot configuration references and destinations; validate membership and posting capability.
- Route authorized content and notifications, inspect webhook/polling status, and expose safe diagnostics.
- Store secrets outside ordinary records; protect webhooks and redact sensitive data.

### Group D — Content and automation

#### 16. Content management
- Create, edit, preview, review, publish, and archive bilingual content.
- Manage assets, metadata, SEO fields, revisions, sanitization, and public/private visibility.

#### 17. Campaign management
- Create and manage campaigns, audiences, channels, schedules, approvals, pause/resume, and closure.
- Respect consent and eligibility; calculate outcomes only from recorded events.

#### 18. Scheduling and publishing
- Schedule, reschedule, cancel, retry, and inspect publishing jobs.
- Preview destination-specific output and track each destination's delivery result.
- Use idempotency, bounded retries, explicit timezones, and persisted delivery attempts.

#### 19. AI assistant and controlled automation
- Provide assistive summaries, classification, draft responses, and suggested next actions.
- Use provider-agnostic adapters and protected credentials.
- Enforce RBAC, scope, audit, data protection, and human approval before external or irreversible actions.
- Test prompt injection, data leakage, and generated-output labeling.

### Group E — Governance and quality

#### 20. Analytics and reporting
- Reports by period, service, status, channel, organization, and other supported dimensions.
- Authorized exports and drill-down to source records.
- Define every metric's source, query, timezone, freshness, and limitations; reconcile aggregates to source rows.

#### 21. Audit and governance
- Searchable audit history by actor, action, resource, and date.
- Safe before/after metadata, privileged-access review, and permission-controlled exports.
- Protect audit integrity and apply reviewed retention rules; never log secrets or unnecessary personal data.

#### 22. Security and risk management
- Review authentication failures, suspicious access, permission changes, and integration/security events.
- Manage supported password/session/security policies and incident triage.
- Apply rate limits, secure token/session lifecycle, relevant CSRF protections, input validation, secret redaction, and dependency scanning.
- Display alerts only when backed by actual event sources.

#### 23. System operations, QA, and production readiness
- Real health/readiness probes, database/storage/integration status, background job visibility, and release health.
- Backup artifacts and isolated restore verification—not placeholder success records.
- CI coverage for unit, integration, API authorization, migration, and frontend smoke tests.
- Release checklist, rollback plan, operational diagnostics, and verified acceptance evidence.

### Phase 1 shared acceptance contract

Every module must be delivered end-to-end, not as a screen-only placeholder:

1. Complete applicable CRUD and lifecycle workflows (use archive, reversal, or immutable records instead of unsafe hard deletion where required).
2. UI, API, validation, persistence, and consistent error/response behavior.
3. Backend authorization for list, detail, create, update, archive/delete, export, and related actions.
4. Audit events for sensitive mutations.
5. Arabic/English localization, correct RTL/LTR, and responsive behavior.
6. Loading, empty, error, success, and permission-denied states.
7. Search, filters, sorting, and server-side pagination where appropriate.
8. Unit, integration, API, authorization, and relevant frontend tests.
9. Documentation, dependency notes, and recorded acceptance evidence.

Use the status vocabulary consistently:
- `NOT_STARTED` — work has not started.
- `IN_PROGRESS` — active implementation.
- `PARTIAL` — some required behavior exists but acceptance is incomplete.
- `IMPLEMENTED` — code and workflows are implemented but not fully verified.
- `VERIFIED` — automated tests and recorded acceptance checks pass.
- `BLOCKED` — an explicit dependency or decision prevents progress; document owner and resolution path.

A module is not VERIFIED because its navigation item or UI exists. Phase 1 is complete only when all 23 modules are VERIFIED or an explicitly approved scope change records a justified exclusion. A BLOCKED module is not silently counted as complete.

### Phase 1 delivery and preservation rules

- Continue from the current repository and working state; do not rebuild, reset, or discard existing work.
- Deliver small, reviewable increments; keep unfinished modules visible in the backlog.
- Phase 1 remains active while later phases proceed where stable contracts allow; do not freeze or abandon its remaining work.
- Use isolated test databases only; never modify production database data/schema or run production migrations during development.
- Do not claim browser/device acceptance until it has actually been performed.
- Deploy only after the relevant changes are reviewed and verified, following the project's release controls.

## 5. Phase 2 — Customer-facing Telegram experiences

**Goal:** complete the customer journey inside Telegram using the shared platform backend.

Scope:
- Telegram Bot conversation flows, onboarding, service discovery, request creation/status, customer assistance, and notifications.
- Telegram Mini App customer workspace, account/profile, service catalog, request submission/tracking, quotations/documents where authorized.
- Verified account linking to the central customer identity.
- Secure webhook or polling operations, bot permissions, destination routing, and delivery diagnostics.
- Arabic/English and RTL/LTR across supported Telegram clients.
- End-to-end tests for identity, permissions, request lifecycle, and delivery failure/retry.

This phase consumes the shared services and domain contracts delivered in Phase 1; it must not create a separate customer database or bypass backend authorization.

## 6. Phase 3 — Customer Portal

**Goal:** deliver the web-based customer workspace using the same identity and business records as Telegram.

Scope:
- Secure registration/sign-in and account recovery according to the approved identity design.
- Customer profile and verified channel linking.
- Service discovery and request creation/tracking.
- Customer documents, quotations, invoices, and payment views only when their underlying workflows are verified.
- Notifications, preferences, history, and support entry points.
- Responsive accessible Arabic/English experience.
- Customer-isolation, authorization, and end-to-end tests.

## 7. Phase 4 — Official Public Website

**Goal:** deliver the public-facing company and service presence.

Scope:
- Company profile, service catalog, contact and inquiry paths.
- Bilingual content and SEO metadata.
- Content sourced from the approved publishing workflow where applicable.
- Responsive accessible pages, performance, and search-engine readiness.
- Clear separation between public content and private customer/admin records.

## 8. Phase 5 — Platform-wide hardening and scale readiness

**Goal:** verify the integrated five-system platform as one secure and recoverable product.

Scope:
- Cross-system end-to-end acceptance and regression testing.
- Security review, dependency scanning, access-control review, and incident readiness.
- Performance/load testing and query/index optimization based on measurements.
- Backup and restore drills, disaster recovery, and rollback verification.
- Monitoring and alerting based on real signals.
- Accessibility, localization, responsive, and browser/device acceptance.
- Operational documentation and production-readiness sign-off.

## 9. Dependency and execution principles

- Authentication, persistence, validation, authorization, audit, localization, and tests are implemented as shared foundations alongside the first module that requires them.
- RBAC and platform settings precede broad administrative access and privileged workflows.
- Organization/branch scope is implemented only after ownership and isolation rules are approved.
- Customer identity and account linking must be stable before completing Telegram and portal journeys.
- Requests depend on services and customer identity; files and quotations depend on request/customer contracts.
- Financial workflows require an approved ledger design and must not be simulated.
- Tasks and staff workload depend on real assignment records.
- Notifications and publishing depend on durable delivery/job records and idempotent workers.
- Analytics depend on authoritative source records and documented metric definitions.
- AI assistance never bypasses authorization, validation, approval, or audit.
- Work may proceed in parallel only when domain contracts and schema dependencies are stable.

## 10. Current delivery status and source of truth

This roadmap defines the approved target scope; it does not assert that the scope is already implemented.

For the current implementation state, use:
- `docs/ADMIN_SYSTEM_DELIVERY_BLUEPRINT.md` for the 23-module delivery contract and acceptance criteria.
- `docs/PHASE_01_MODULE_01_DASHBOARD_STATUS.md` for the Dashboard's recorded status.
- `docs/MODULE_02_USERS_ACCOUNTS_STATUS.md` for Module 02 implementation status and remaining acceptance scope.
- GitHub pull requests, CI runs, and deployment records for verifiable delivery evidence.

Update module status only when evidence exists. Keep planned, implemented, and verified work clearly separated.


---

# Detailed implementation specification — Module 02: Users & Accounts

**Module:** 02 of the 23 Administration modules in Phase 1  
**Status:** Approved target specification; implementation status must be evidenced separately  
**Primary domain:** Identity and account lifecycle management  
**Architecture:** Existing FastAPI modular monolith, shared identity, shared database, existing frontend architecture  
**Related modules:** 01 Dashboard; 03 Roles & Permissions; 04 Platform Settings; 05 Organizations & Branches; 07 Customer Management; 08 Request Management; 12 Staff Management; 14 Communication & Notifications; 15 Telegram; 21 Audit & Governance; 22 Security & Risk; 23 System Operations & QA.

This specification expands the short Module 02 scope above. It is the implementation reference for Module 02 and must be read together with the five-system architecture and Phase 1 shared acceptance contract. It does not claim that any listed capability is already implemented.

## 11. Module purpose and boundaries

Deliver a secure, centralized system for managing platform user identities and accounts from creation through activation, suspension, recovery, session revocation, identity linking, deactivation, archival, and legally permitted deletion.

This is not merely a user table with create/edit buttons. It is an identity and access lifecycle capability integrated with the rest of EHTERAF.

The module owns user-account administration and its lifecycle. It integrates with, but does not replace:
- Module 03 for role catalog, permission catalog, role-permission rules, and privileged RBAC governance.
- Module 07 for the customer business profile and customer-specific lifecycle.
- Module 12 for the employee/staff business profile and employment/assignment information.
- Module 14 for notification creation, delivery, retry, and delivery evidence.
- Module 15 for Telegram bot/channel configuration and delivery operations.
- Module 21 for authoritative audit history and governance.
- Module 22 for security-event triage, risk policy, and incident management.

A user account, a customer profile, a staff profile, a role, and an external channel identity are distinct concepts. They may be related, but must not be collapsed into one record or duplicated as independent login identities without an approved design.

## 12. Functional domains

The module must cover these twelve domains, with explicit implementation status for each:
1. User Directory.
2. Account Lifecycle.
3. User Profiles.
4. Authentication integration.
5. Session Management.
6. External Identity Linking.
7. Access Control integration.
8. Account Security Monitoring.
9. Audit and Activity History.
10. Bulk Operations.
11. Import and Export.
12. Account Preferences.

## 13. User Directory

### 13.1 Directory fields

Provide a permission-filtered, paginated directory with safe fields:
- Internal User ID.
- Username.
- First and last name / display name.
- Email and verification state.
- Phone and verification state.
- Profile image reference where supported.
- Account type/category.
- Assigned roles (only where the viewer may inspect them).
- Account status.
- Created and updated timestamps.
- Last successful login and last activity when reliably recorded.
- Linked channel/provider indicators without exposing tokens or secrets.
- Organization and branch scope only after the corresponding scope model is approved and implemented.

Never expose password hashes, reset tokens, verification codes, access/refresh tokens, secret credentials, or private provider payloads in directory responses.

### 13.2 Search, filters, sorting, and pagination

Support server-side:
- Search by user ID, username, name, email, and phone, with safe normalization.
- Filters for status, account type, role, creation date, last-login date, and verified contact state.
- Filters for linked identity/provider state.
- Organization/branch filters only when approved scope enforcement exists.
- Sorting by supported fields using an allowlist.
- Stable pagination with bounded page size and database-side count.
- Empty, loading, error, and permission-denied states.

Do not load the full user population into the browser. Escape or safely parameterize search terms; do not construct unsafe SQL from user input. Define whether email/username matching is case-insensitive and enforce the same policy in validation and database constraints.

### 13.3 Directory actions

Per-row actions must be permission-aware and include view, edit, activate, suspend, reactivate, deactivate, lock/unlock, session management, identity management, and archive where applicable. Each action must also be enforced server-side. Destructive or security-sensitive actions require a confirmation step and a recorded reason where policy requires it.

## 14. Create Account

The creation workflow must support:
- Username and required identity fields.
- First name, last name, email, phone, profile image reference, language, and timezone as applicable.
- Account type/category.
- Initial status subject to approved invitation/activation policy.
- Optional initial role only when the actor is authorized to assign that role.
- Organization/branch association only under an approved scope model.
- Optional account expiry for temporary accounts.
- Invitation or secure password-setup flow where supported.

Validation requirements:
- Required-field and length validation.
- Email and phone normalization/format validation.
- Username/email uniqueness consistent with the canonical identity policy.
- Reject duplicate external identity ownership.
- Validate requested role and ensure the actor cannot grant privileges they do not possess.
- Validate account type and status against supported enumerations.
- Prevent self-privilege escalation and unauthorized creation of privileged accounts.
- Return field-level validation errors without leaking whether sensitive accounts exist beyond the permitted response policy.

Password requirements:
- Never store or log plaintext passwords.
- Use the project's reviewed password hashing implementation; Argon2id is an acceptable target where compatible with the current security baseline.
- Apply configured password policy.
- Prefer single-use, time-limited password setup links over transmitting passwords.
- Never send a password in email, Telegram, logs, or audit records.
- Do not silently assign a weak default password.

## 15. Update Account and Profile

Support partial updates without resetting omitted fields. Separate account/security fields from personal profile/preferences where that improves ownership and validation.

Editable fields may include:
- Display and legal names as applicable.
- Username under the approved rename policy.
- Email and phone, with re-verification when changed.
- Profile image reference.
- Language and timezone.
- Account type and supported status.
- Approved organization/branch associations.
- Expiry and activation metadata.
- Role assignments only through authorized RBAC integration.

Every mutation must validate current state, actor permissions, target scope, and concurrency. Record safe before/after values for sensitive changes. Never include secrets, hashes, raw tokens, or unnecessary personal data in audit payloads. Trigger session invalidation or re-authentication when the security policy requires it.

## 16. Account lifecycle and status model

The lifecycle must support explicit, documented states. Proposed states are:
- `PENDING`: awaiting invitation acceptance or verification.
- `ACTIVE`: allowed to authenticate, subject to policy.
- `SUSPENDED`: administratively paused for a defined reason/period.
- `LOCKED`: security lock due to policy or authorized intervention.
- `DEACTIVATED`: administratively disabled.
- `EXPIRED`: account validity period has ended.
- `DELETION_REQUESTED`: a privacy/deletion request is being reviewed.
- `ARCHIVED`: retained but no longer operational, according to retention policy.

The final enum must be reconciled with existing model values and migrations before implementation. Do not introduce incompatible status strings or silently reinterpret existing records.

Supported lifecycle actions:
- Activate.
- Suspend.
- Reactivate.
- Lock and unlock.
- Deactivate.
- Expire.
- Archive and restore where policy allows.
- Request deletion and execute approved deletion/anonymization where legally permitted.

Lifecycle invariants:
- Suspended, locked, deactivated, expired, and archived accounts must not authenticate.
- Existing sessions and tokens must be revoked or rendered unusable according to the security policy when an account is disabled or locked.
- Reactivation must not restore roles that were previously removed.
- Every sensitive transition records actor, timestamp, reason, prior state, resulting state, and outcome.
- Protect the last active Super Admin and other break-glass accounts defined by policy.
- Do not hard-delete users referenced by requests, invoices, payments, audit records, or other retained business records.
- Use archive, anonymization, or compensating workflows when physical deletion would violate integrity or retention obligations.

## 17. Authentication integration

Module 02 integrates with the existing authentication module; it must not create a parallel login system.

Required capabilities and acceptance checks:
- Username/email login according to the canonical identity policy.
- Verify account status and expiry before issuing a usable session/token.
- Generic authentication failure responses that do not disclose account existence.
- Brute-force controls and rate limiting.
- Secure password-reset request and completion.
- Single-use, time-limited reset tokens stored safely (prefer hashed token material).
- Invalidate prior reset tokens when a new reset is issued.
- Avoid account enumeration in reset responses.
- Email and phone verification with expiring, single-use codes and attempt limits.
- Record authentication events without recording credentials.
- Password change/recovery must apply session revocation policy.
- MFA architecture and policy must be documented; supported options may include TOTP and recovery codes. Do not show MFA as enabled unless the complete enrollment, verification, recovery, and enforcement flow exists.
- Privileged users should be subject to an approved MFA policy.

## 18. Session management

Provide a session inventory and real revocation capability.

Session metadata, where available and privacy-approved:
- Session identifier.
- User identifier.
- Created/issued time and expiry.
- Last activity.
- Device/browser/OS summary.
- IP address or privacy-preserving representation according to policy.
- Session status.
- Revocation timestamp, actor, and reason.

Operations:
- List active sessions and permitted historical sessions.
- Revoke one session.
- Revoke all sessions for an account.
- Revoke sessions after password reset/change, account suspension/deactivation/lock, or security incident according to policy.
- Notify the user of important security events where supported.
- Prevent revoked sessions from continuing to access protected endpoints.

JWT note: deleting a token from browser storage is not server-side revocation. If JWTs are used, implement a real session registry, token-version/revocation mechanism, or another reviewed design; use bounded token lifetimes and safe refresh-token rotation if refresh tokens exist. Do not invent a sessions API that merely returns fabricated or inferred sessions.

## 19. External identity linking

Support a central user identity linked to verified external identities, especially Telegram, without creating duplicate customers when channels change.

Identity record should contain only necessary data:
- Internal identity record ID.
- Internal user ID.
- Provider name.
- Provider subject/user ID.
- Verification/link status.
- Created/linked and last-used timestamps.
- Revocation/unlink timestamp and actor where relevant.
- Minimal provider metadata required for operation.

Linking workflow:
1. Authenticated user initiates linking.
2. Backend creates a cryptographically random, single-use, short-lived challenge.
3. User proves control of the external account through the provider's supported flow.
4. Backend validates provider proof server-side.
5. Backend atomically verifies that the provider identity is not already linked to another account.
6. Link is committed and audited.
7. Unlinking requires re-authentication or an equivalent approved proof and must not orphan the user from all recovery methods.

Telegram-specific requirements:
- Validate Telegram Mini App `initData` on the backend using the official verification algorithm and freshness checks.
- Never trust client-submitted Telegram user fields without cryptographic verification.
- Protect bot webhooks with the configured secret mechanism and replay controls.
- Do not accept a Telegram numeric ID supplied by the browser as proof of ownership.
- Do not expose bot tokens or provider secrets in the UI/API.
- Define safe account recovery if Telegram is the only linked channel.

Identity invariants:
- One provider subject cannot belong to multiple internal users.
- Similar names or matching unverified contact fields are not sufficient proof to merge accounts.
- Account merge is a separate privileged, reviewable operation with explicit evidence, collision handling, reference migration plan, and immutable audit.
- Prevent duplicate customer profiles when the same verified person uses website and Telegram channels.

## 20. RBAC integration and privilege safety

Module 02 consumes Module 03's role and permission services. It may display assigned/effective roles and offer permitted assignment actions, but does not own the role/permission catalog.

Proposed permission families (reconcile with existing permission constants before adding anything):
- `users.read`
- `users.create`
- `users.update`
- `users.activate`
- `users.suspend`
- `users.deactivate`
- `users.archive`
- `users.delete` (only if policy permits)
- `users.assign_roles`
- `users.manage_sessions`
- `users.link_identity`
- `users.unlink_identity`
- `users.view_security`
- `users.manage_security`
- `users.import`
- `users.export)

Security rules:
- Enforce permissions in every backend route/service, not only by hiding UI controls.
- Deny by default.
- Prevent actors from granting roles or permissions above their authority.
- Prevent self-elevation and unsafe changes to the acting account.
- Protect the last active Super Admin and designated break-glass accounts.
- Re-evaluate permissions after role changes and revoke/refresh sessions or authorization cache according to policy.
- Audit all role assignment changes.
- Test cross-user IDOR, cross-organization access, and privilege escalation.

## 21. Account security monitoring

Capture genuine security events, such as:
- Successful and failed login attempts.
- Account lock/unlock and suspension.
- Password reset/change completion (never password values).
- Email/phone changes and verification.
- Role/privilege changes.
- New session and session revocation.
- External identity link/unlink.
- Unusual or policy-violating access where a reliable detection rule exists.
- Administrative actions affecting accounts.

Provide authorized operators with relevant event history and safe response actions:
- Lock account.
- Revoke sessions.
- Require password reset/re-authentication.
- Revoke recovery challenges/tokens.
- Escalate an incident to Module 22.

Automated high-impact responses require an approved policy, clear thresholds, audit, false-positive handling, and recovery path. Do not claim anomaly detection without a real signal and implemented detection logic.

## 22. Activity timeline and audit

Keep three concepts distinct:
- Audit Log: authoritative record of administrative/business mutations.
- Activity Timeline: user-centered presentation of relevant events.
- Security Events: security-significant events routed to Module 22.

Show authorized events such as account creation, profile updates, lifecycle transitions, authentication outcomes, role changes, identity linking, and session revocation.

Audit requirements:
- Actor, target user/resource, action, timestamp, outcome, correlation/request ID, and safe metadata.
- Before/after values only for approved non-secret fields.
- Reason/comment for sensitive administrative actions.
- Transactional or reliable-outbox behavior so a successful mutation cannot silently lose its audit event.
- Search/filter/pagination at database level.
- Export permission and access logging.
- Retention and integrity policy.
- Never store plaintext passwords, password hashes, tokens, verification codes, bot tokens, private keys, or full sensitive provider payloads.

## 23. Bulk operations

Support permission-controlled bulk actions where operationally justified:
- Activate.
- Suspend.
- Deactivate.
- Assign/remove an allowed role.
- Archive.
- Export.

Requirements:
- Bounded batch size and rate.
- Preview target count and expected action.
- Confirm sensitive actions.
- Re-check each target's scope and permissions at execution time.
- Protect the last active Super Admin and protected accounts.
- Use transaction boundaries appropriate to the operation; report per-item success/failure.
- Use idempotency or duplicate-submission protection.
- Record a parent operation and per-item outcomes.
- Never report total success when some rows failed.
- Avoid long synchronous requests; use a durable job for large imports/batches if needed and already supported by the architecture.

## 24. Import and export

Import:
- Provide a versioned CSV template; XLSX may be added if justified by current dependencies and architecture.
- Validate file type, size, encoding, headers, row count, and every field.
- Normalize identifiers and detect duplicate rows and existing accounts.
- Preview valid/invalid rows before committing.
- Never grant privileged roles automatically from untrusted import data.
- Produce a downloadable result report with row-level errors.
- Audit the actor, file metadata, counts, and outcome without storing unnecessary personal data in logs.

Export:
- CSV and, if approved, XLSX.
- Server-side filtering and pagination/streaming for large datasets.
- Field-level permission checks and data minimization.
- Protect generated files and download URLs; apply expiry and access control.
- Audit who exported what scope and when.
- Exclude hashes, tokens, secret values, and fields the actor cannot view.

## 25. Account preferences

Support user-level preferences where relevant:
- Arabic/English language.
- Correct RTL/LTR rendering.
- Timezone.
- Date and number formatting where user-overridable.
- Notification preferences by supported channel.
- Light/dark theme if this preference is shared by the existing frontend.
- Privacy choices allowed by platform policy.

Keep user preferences distinct from global settings in Module 04 and organization/branch policy in Module 05. Server-side defaults must remain authoritative where preferences cannot override security or legal policy.

## 26. Required administration UI

Required screens/workspaces:
1. Users Directory.
2. Create User.
3. User Profile / Details.
4. Edit User.
5. Account & Status Management.
6. Account Security.
7. Active and historical Sessions.
8. Linked Identities.
9. Roles & Effective Access summary.
10. Activity Timeline and Audit History.
11. Bulk Operations review.
12. Import / Export.

User profile detail should use tabs/sections:
- Overview.
- Personal Information.
- Account & Status.
- Roles & Access.
- Sessions.
- Linked Identities.
- Security.
- Activity.
- Audit History.

UI/UX acceptance:
- Match the approved EHTERAF premium enterprise/SaaS visual system and existing admin shell.
- Full Arabic and English copy, not partial translation.
- Correct RTL/LTR layout, forms, tables, icons, breadcrumbs, and drawers.
- Responsive desktop, laptop, tablet, and mobile behavior.
- Light and dark themes consistent with the application.
- Loading, empty, error, success, validation, and permission-denied states.
- Confirmation for sensitive actions and clear reason capture where required.
- Preserve search/filter/page context after mutations where practical.
- No decorative controls that do not perform real actions.
- No fake metrics, fake last-login/session data, or placeholder success.

## 27. Backend architecture and API contract

Preserve the existing FastAPI modular monolith and current application boundaries:
- API routes: request parsing, response mapping, dependencies.
- Pydantic schemas: input/output validation.
- Application services: lifecycle and use-case rules.
- Repositories: database access and query composition.
- Existing SQLAlchemy models: canonical persistence entities.
- Authorization dependencies/services: backend enforcement.
- Audit service: safe, reliable event recording.
- Notification application service: delivery decoupled from account routes.
- Provider adapters: verified external identity operations.

The existing `/api/v1/admin/users` routes and existing authentication APIs must be inspected and extended. Do not create duplicate endpoints or parallel user services without a documented reason.

Candidate API contract (adapt to existing conventions and avoid duplicate routes):
| Method | Candidate endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/admin/users` | Search/filter/paginate users |
| POST | `/api/v1/admin/users` | Create account |
| GET | `/api/v1/admin/users/{id}` | Read account |
| PATCH | `/api/v1/admin/users/{id}` | Partial update |
| POST | `/api/v1/admin/users/{id}/activate` | Activate |
| POST | `/api/v1/admin/users/{id}/suspend` | Suspend |
| POST | `/api/v1/admin/users/{id}/deactivate` | Deactivate |
| POST | `/api/v1/admin/users/{id}/reactivate` | Reactivate |
| POST | `/api/v1/admin/users/{id}/lock` | Security lock |
| POST | `/api/v1/admin/users/{id}/unlock` | Unlock |
| GET | `/api/v1/admin/users/{id}/sessions` | List sessions |
| DELETE | `/api/v1/admin/users/{id}/sessions/{session_id}` | Revoke one session |
| POST | `/api/v1/admin/users/{id}/sessions/revoke-all` | Revoke all sessions |
| GET | `/api/v1/admin/users/{id}/identities` | List linked identities |
| POST | `/api/v1/admin/users/{id}/identities` | Link verified identity |
| DELETE | `/api/v1/admin/users/{id}/identities/{identity_id}` | Unlink identity |
| GET | `/api/v1/admin/users/{id}/activity` | Activity timeline |
| GET | `/api/v1/admin/users/{id}/audit` | Authorized audit history |
| POST | `/api/v1/admin/users/bulk-actions` | Bounded bulk action |
| POST | `/api/v1/admin/users/import` | Validated import |
| GET | `/api/v1/admin/users/export` | Authorized export |

These are candidate contracts, not an instruction to implement every route mechanically. Use appropriate HTTP semantics, schemas, status codes, error formats, idempotency, and existing API conventions. A successful create/update response must contain only safe fields. A conflict should return a stable conflict response (for example HTTP 409) without disclosing protected information.

Every route must have authentication, explicit permission checks, scope checks where applicable, validation, safe error handling, and tests. Hiding a UI control is never a substitute for backend authorization.

## 28. Data model and persistence requirements

First inspect and reuse current models/tables. The following are conceptual entities, not an instruction to create all of them if equivalent structures already exist:
- Users (canonical account identity).
- User Profiles (only if personal profile separation is justified).
- Roles and User Roles (owned by/integrated with Module 03).
- External Identities.
- User Sessions / token revocation records.
- Password Reset Tokens.
- Email Verification Tokens.
- Phone Verification Tokens.
- Login Attempts.
- Security Events.
- User Preferences.
- Account Lifecycle Events.
- Audit Logs (shared with Module 21).

Conceptual relationships:
- One user may have zero or one profile record depending on the existing model.
- One user may have multiple sessions over time.
- One user may have multiple verified external identities, subject to provider-specific uniqueness.
- One user may have multiple roles under RBAC policy.
- One user may have preferences and security/audit events.
- Audit actor and audit target are separate concepts; an event may be performed by one user against another.

Persistence rules:
- Preserve existing primary-key conventions (UUID if already canonical).
- Use foreign keys and uniqueness constraints for identity invariants.
- Add indexes based on measured search/filter queries.
- Store timestamps consistently in UTC and render in user timezone.
- Use transactions for multi-step lifecycle/linking changes.
- Handle concurrent updates and uniqueness races safely.
- Avoid N+1 queries and materializing all rows for counts/pagination.
- Never persist plaintext passwords, reset tokens, verification codes, or provider secrets.
- Define retention/deletion/anonymization behavior before destructive migrations.
- Any schema change requires a reviewed, reversible Alembic migration and isolated-database upgrade/downgrade tests.
- Never run development migrations or test suites against production databases.

## 29. Security and privacy requirements

Security acceptance must include:
- Secure password hashing using the project's approved implementation (Argon2id target where compatible).
- Brute-force protection and rate limits for login, reset, verification, and linking.
- Single-use, expiring reset/verification/link challenges.
- Secure session and refresh-token lifecycle, revocation, and cookie settings where applicable.
- CSRF protection where cookie-based authentication requires it.
- Correct CORS and trusted-origin configuration.
- Input validation and safe output encoding.
- Deny-by-default authorization on every protected API.
- Protection against IDOR and cross-scope data access.
- Privilege-escalation and last-Super-Admin protections.
- Secret redaction in logs, traces, errors, and audit metadata.
- Privacy minimization for IP/device metadata and defined retention.
- Safe account recovery when external identity providers are unavailable.
- Dependency/security scanning and documented threat review.
- No Firebase.

## 30. Notifications and integration behavior

Account-related notifications must be created through Module 14's application service, not sent directly from user route handlers.

Potential events:
- Account invitation/creation.
- Activation and suspension/deactivation.
- Password reset/change confirmation.
- Email/phone verification.
- New login/session security notice.
- Session revocation.
- External identity linking/unlinking.

Track states only when backed by delivery evidence:
- Created.
- Queued.
- Sent.
- Delivered.
- Failed.
- Retried.

Enqueueing is not delivery. Provider failure must not corrupt the account transaction. Use durable outbox/queue patterns already supported by the architecture, idempotency, bounded retry, and safe failure visibility.

## 31. Performance, reliability, and operational behavior

- Database-side search, sorting, and pagination.
- Appropriate indexes verified against actual query patterns.
- Avoid N+1 queries and unnecessary eager loading.
- Bound page sizes, batch sizes, file sizes, and request durations.
- Use durable background jobs only where the current architecture supports them and the operation warrants it.
- Apply idempotency or duplicate-submission protection to sensitive operations.
- Use transaction boundaries and reliable audit/outbox behavior.
- Return consistent error responses and correlation IDs.
- Do not expose stack traces or secrets to clients.
- Distinguish unavailable provider/service state from successful operation.
- Record operational failures without leaking personal or authentication data.

## 32. Test strategy and mandatory scenarios

### Unit tests
- Valid account creation.
- Duplicate username/email rejection.
- Identity normalization and uniqueness.
- Partial update preserves omitted fields.
- Lifecycle transition policy.
- Invalid transition rejection.
- Role assignment constraints.
- Last active Super Admin protection.
- Reset/verification/link challenge expiry and one-time use.
- External identity uniqueness.
- Session revocation policy.
- Safe audit payload generation.

### API/integration tests
- List, search, filter, sort, paginate.
- Create, read, update.
- Activate, suspend, reactivate, deactivate, lock, unlock, archive.
- Sessions list/revoke/revoke-all.
- Identity link/unlink and duplicate ownership.
- Activity and audit access control.
- Bulk action partial success/failure.
- Import validation and export permissions.
- Notification failure does not corrupt account lifecycle.
- All routes reject unauthenticated and unauthorized actors appropriately.

### Security tests
- Ordinary user cannot access admin endpoints.
- Actor cannot assign a role above their authority.
- Actor cannot elevate themselves.
- Cross-user IDOR is denied.
- Cross-organization/branch access is denied where scope applies.
- Last Super Admin cannot be disabled or stripped of required protection.
- Expired, used, or revoked reset tokens are rejected.
- Revoked sessions cannot continue to access protected endpoints.
- Locked/deactivated/expired accounts cannot authenticate.
- Telegram identity proof is verified server-side.
- Duplicate provider identity cannot link to another account.
- Secrets/hashes/tokens never appear in responses or logs.

### Frontend and end-to-end tests
- Directory navigation and responsive layout.
- Search, filters, sort, pagination.
- Create/edit and field validation.
- Lifecycle confirmation and resulting access behavior.
- Sessions and identity views.
- Role visibility and permission-denied behavior.
- Arabic/English and RTL/LTR.
- Light/dark themes.
- Loading/empty/error/success states.
- Complete scenario: authorized admin creates a user; user appears in directory; profile is updated; account is suspended; login is rejected; account is reactivated; permitted login succeeds; a session is revoked; audit history shows each mutation.

Test databases must be isolated and synthetic. Do not run tests against production data or apply migrations to production as part of development verification.

## 33. Definition of Done and verification status

Module 02 can be marked `VERIFIED` only when evidence proves all applicable requirements below:
- Directory, search, filtering, sorting, and server-side pagination.
- Complete create/read/update and safe lifecycle operations.
- Profile and preference management.
- Authentication/recovery/verification integration.
- Real session inventory and server-enforced revocation.
- Verified external identity linking/unlinking.
- Backend RBAC and privilege safety.
- Security events and account protections.
- Complete audit trail for sensitive mutations.
- Safe bulk operations.
- Validated import/export with permission controls.
- Notification integration and honest delivery states.
- Arabic/English, RTL/LTR, responsive and theme acceptance.
- Unit, integration, authorization, security, and relevant frontend/E2E tests.
- API and operational documentation.
- CI checks pass and evidence is attached to the implementation PR.
- Browser/device acceptance is claimed only after it has actually been performed.

Use the roadmap status vocabulary:
- `NOT_STARTED`
- `IN_PROGRESS`
- `PARTIAL`
- `IMPLEMENTED`
- `VERIFIED`
- `BLOCKED`

A route, model, screen, or passing isolated test alone does not establish module completion. Planned, implemented, and verified capabilities must be reported separately.

## 34. Delivery plan for Module 02

Deliver in small, reviewable increments, reusing existing code:
1. **Inventory and gap analysis:** inspect existing admin user routes, authentication, models, schemas, permissions, frontend, migrations, and tests; create a file/API/table/evidence matrix.
2. **Core account workflows:** finish directory, create/read/update, validation, and lifecycle transitions.
3. **Authentication and sessions:** recovery/verification integration, session registry/revocation, and security policies.
4. **External identities:** verified Telegram and future provider linking, uniqueness, unlinking, and recovery.
5. **RBAC and audit:** align existing permission names, enforce privilege boundaries, and record sensitive changes.
6. **Administration UX and data operations:** profile tabs, bulk operations, import/export, localization, responsive and theme behavior.
7. **Verification and release:** isolated tests, security tests, frontend/E2E checks, CI, reviewable PR, deployment, and post-deployment smoke checks.

Do not rebuild the project, reset branches, discard existing changes, duplicate existing models/routes, or change frameworks/dependencies without a reviewed ADR. Preserve all existing functionality and data. Keep production database schema/data/config untouched unless separately and explicitly approved. Merge and deploy only after review and verification; deployment success does not itself prove functional acceptance.

## 35. Required implementation evidence record

For each requirement, maintain a traceable record with:
- Requirement ID and description.
- Status from the approved status vocabulary.
- Frontend file/route/component.
- API route and permission.
- Application service/use case.
- Model/table/migration (or explanation why no schema change is needed).
- Validation and lifecycle rules.
- Audit/security behavior.
- Unit/integration/security/frontend test references.
- CI run and PR reference.
- Manual browser/device acceptance evidence, if performed.
- Known limitations, dependencies, and next action.

The initial inventory is not to be guessed from this specification. It must be derived from the current `main` code and test evidence. The current repository already contains an admin users route and authentication foundations; those are starting points to inspect and extend, not proof of full Module 02 completion.
