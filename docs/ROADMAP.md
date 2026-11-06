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
- GitHub pull requests, CI runs, and deployment records for verifiable delivery evidence.

Update module status only when evidence exists. Keep planned, implemented, and verified work clearly separated.
