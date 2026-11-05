# EHTERAF Administration System — Delivery Blueprint

**Repository:** `MoatasemTAlmasani/academic-telegram-platform`  
**Baseline:** approved `docs/EHTERAF_MASTER_REFERENCE.md`  
**Delivery branch:** `feature/admin-system-delivery`  
**Architecture:** existing FastAPI modular monolith, shared PostgreSQL persistence, database-backed RBAC  
**Status vocabulary:** NOT_STARTED / IN_PROGRESS / PARTIAL / IMPLEMENTED / VERIFIED / BLOCKED

This blueprint expands the approved 23-stage administration roadmap into deliverable modules. It is a delivery contract, not a claim that the listed capabilities already exist.

## 1. Delivery rules

1. Continue the existing repository and preserve existing APIs, pages, data, and integrations.
2. Every feature is end-to-end: UI, API, validation, authorization, persistence, audit, localization, and tests.
3. Frontend visibility is never an authorization boundary. Every protected API enforces permission checks.
4. Use persisted business records only. Never invent KPIs, customers, testimonials, financial balances, delivery status, or operational health.
5. Every screen must support loading, empty, error, success, and permission-denied states.
6. Arabic and English are first-class; RTL/LTR must be tested, not inferred from text direction alone.
7. Keep the modular monolith. Introduce a new service, database, or foundational technology only through a reviewed ADR.
8. Do not add Firebase. Keep Telegram integrations behind existing application services and secure adapters.
9. Schema changes require reversible Alembic migrations and isolated-database tests. Never run migrations against production as part of development.
10. A capability is VERIFIED only after automated tests and a recorded acceptance check. Code existing is only IMPLEMENTED.
11. Do not remove a legacy route or screen until usage, dependencies, replacement behavior, and a safe deprecation path are proven.
12. No production deployment or production configuration mutation is part of this delivery branch.

## 2. Shared administration foundation

### Navigation and shell
- One authenticated shell with responsive sidebar, top bar, breadcrumbs, global search entry, notification entry, profile/session controls, and quick actions.
- Navigation nodes are generated from a centralized module registry and filtered by the user's effective permissions.
- Direct URL access must still be denied by the backend when permission is missing.
- Persist language, direction, theme, and permitted user preferences without storing credentials in browser storage beyond the currently approved auth design.

### Design system
- Premium Enterprise + Modern SaaS visual direction.
- Arabic-first typography with Cairo and a legible Latin fallback; consistent spacing, type scale, color tokens, elevation, focus states, tables, forms, dialogs, toasts, badges, charts, and empty states.
- Responsive layouts for desktop, tablet, and mobile; accessible keyboard navigation and visible focus.
- Light/dark themes with semantic tokens, not duplicated hard-coded colors.

### Shared backend contracts
- Consistent pagination, filtering, sorting, validation errors, and response envelopes.
- Central authorization dependency and permission catalog.
- Audit events for privileged mutations, including actor, action, resource, timestamp, request context, and safe before/after metadata.
- Notification records and delivery attempts must be distinguished.
- Query performance budgets and indexes must be justified by measured access patterns.

## 3. The 23 administration stages

### Group A — Foundation and control

#### Stage 01 — Super Admin executive dashboard
**Outcome:** trustworthy operational overview, not a decorative mock dashboard.

**Workflows**
- Sign in and load an authorization-aware dashboard.
- Select a supported reporting period and refresh metrics.
- Drill down from KPI/chart to the corresponding filtered operational list.
- Review recent activity and actionable alerts.

**Data and APIs**
- Aggregate only existing customer, request, service, quotation, staff, and audit records.
- Add explicit date-window/filter contracts and consistent timezone boundaries.
- Revenue, receivables, staff performance, branch performance, and integration health remain unavailable until their authoritative source records exist.

**Acceptance**
- KPI totals reconcile to filtered source queries.
- Date boundaries, empty data, null values, and timezone handling are tested.
- Every chart has a text equivalent and links to its source list.
- Dashboard access and each drill-down endpoint enforce the relevant permission.
- No sample or fabricated operational values appear in production UI.

#### Stage 02 — Users and accounts
**Outcome:** safe lifecycle management for platform identities.

**Workflows**
- Search/filter/paginate users; view profile and linked channels.
- Create authorized staff/admin/customer accounts.
- Update profile, status, and account metadata.
- Suspend/reactivate accounts and revoke active sessions where session infrastructure supports it.
- Resolve duplicate identities through a reviewed account-linking workflow.

**Data and APIs**
- Reuse central User identity and existing Telegram identity fields.
- Passwords are hashed server-side; password hashes and secrets are never serialized.
- Account linking must be verified and must not create duplicate customers.

**Acceptance**
- Unique username/email conflicts are handled safely.
- Users cannot grant themselves higher roles or permissions.
- Soft-deleted/suspended accounts are handled consistently.
- Mutations create audit events; list/detail responses exclude secrets.

#### Stage 03 — Roles and permissions (RBAC)
**Outcome:** centrally managed, least-privilege authorization.

**Workflows**
- List roles and permission catalog.
- Inspect effective permissions before applying changes.
- Assign/remove roles from users and permissions from roles.
- Protect the last active super-admin path and prevent accidental lockout.
- Review role-change audit history.

**Data and APIs**
- Existing Role, Permission, user_roles, and role_permissions records remain authoritative.
- Separate permission to manage RBAC from permission merely to enter the admin console.
- Permission changes are transactional and audited.
- Future organization/branch data scopes are explicit policy constraints, not UI filters.

**Acceptance**
- Anonymous, insufficient-permission, and authorized cases are tested.
- Privilege escalation, self-escalation, last-admin lockout, unknown permission, and stale-token cases are tested.
- UI and API return the same effective permission set.

#### Stage 04 — Platform-wide settings
**Outcome:** validated, auditable configuration without hidden hard-coded behavior.

**Workflows**
- Read and update supported platform settings.
- Validate locale, timezone, contact details, URLs, and integration settings.
- Preview display-affecting changes.
- Review change history and safely restore supported prior values.

**Data and APIs**
- Classify settings as public, operational, or secret.
- Secrets remain in environment/secret storage and are never returned to browsers.
- Use explicit settings schemas, defaults, validation, and audit events.

**Acceptance**
- Partial updates preserve omitted values.
- Invalid settings are rejected with field-level errors.
- Sensitive values are masked and excluded from logs/audit payloads.
- Settings changes do not silently alter unrelated modules.

#### Stage 05 — Organizations and branches
**Outcome:** controlled organizational structure for the approved hybrid business model.

**Workflows**
- Define organizations, branches, ownership, status, and contact information.
- Assign users and staff to allowed scopes.
- Switch active scope where permitted.
- View scope-aware records and prevent cross-organization access.

**Data and APIs**
- Do not introduce speculative multi-tenancy.
- First document the organization ownership and data-boundary ADR.
- Add schema only after scope rules, migration path, and backward compatibility are approved.

**Acceptance**
- Cross-scope reads and writes are denied by backend tests.
- Existing EHTERAF-operated records remain accessible under the initial organization model.
- Scope changes are audited.

### Group B — Customers, services, and requests

#### Stage 06 — Service catalog management
**Outcome:** complete service lifecycle and public/admin consistency.

**Workflows**
- Create, edit, categorize, activate/deactivate, and archive services.
- Manage bilingual names/descriptions, pricing rules where supported, required inputs, and display order.
- Preview how active services appear to customers.

**Data and APIs**
- Reuse existing Service and Category models where sufficient.
- Do not imply fixed pricing where a quotation is required.
- Validate references and prevent deletion of services referenced by requests.

**Acceptance**
- Public catalog and admin view use the same authoritative records.
- Inactive services cannot receive new requests unless explicitly allowed.
- Mutations are audited and tested.

#### Stage 07 — Customer management and identity linking
**Outcome:** one customer record across web and Telegram channels.

**Workflows**
- Search customer profile and view request/document history.
- Link/unlink a channel through proof of account ownership.
- Correct profile information with audit trail.
- Handle duplicate candidates through a controlled merge process.

**Data and APIs**
- Reuse central User/customer identity.
- Keep channel identifiers unique and never trust a submitted Telegram ID without verification.
- Avoid destructive merges; preserve references and provenance.

**Acceptance**
- Channel linking cannot hijack another account.
- Duplicate linking is idempotent.
- Sensitive personal data is permission-scoped and not exposed in broad lists.

#### Stage 08 — Request management
**Outcome:** reliable request lifecycle and operational ownership.

**Workflows**
- Search/filter requests; view complete request timeline and files.
- Validate and apply allowed status transitions.
- Set priority, deadline, internal notes, and assignment when assignment is implemented.
- Notify the customer through configured channels after committed state changes.
- Handle cancellation, rejection, completion, and reopening according to policy.

**Data and APIs**
- Existing ServiceRequest is the source of truth.
- Formalize transition rules and history before adding complex workflow states.
- Move external notification delivery out of the critical database transaction; track delivery result separately.
- Do not claim staff performance until assignment and event history exist.

**Acceptance**
- Invalid transitions and unauthorized updates are rejected.
- Notification failures do not roll back a valid request update.
- Every state change is auditable and idempotent where retried.
- Customer-facing status is consistent across portal and Telegram.

#### Stage 09 — Files and document management
**Outcome:** secure lifecycle for customer and operational documents.

**Workflows**
- Upload, validate, preview/download, associate, version, and archive files.
- Restrict access by owner, request, and permission.
- Record retention and deletion outcomes.

**Data and APIs**
- Reuse existing file abstractions; storage provider must be environment-configured.
- Validate size, MIME type, extension, content signature, and malware-scanning status where available.
- Use short-lived authorized download links; never expose private object paths.

**Acceptance**
- Unauthorized cross-customer downloads fail.
- Dangerous file types and oversized files are rejected.
- Upload/download events are auditable.

#### Stage 10 — Quotations management
**Outcome:** controlled quote lifecycle tied to requests.

**Workflows**
- Draft, revise, send, expire, accept, reject, and cancel quotations.
- View quote history and customer decision.
- Generate printable/downloadable quote documents from persisted values.

**Data and APIs**
- Reuse Quote model and request relationship.
- Validate currency, amount precision, expiry, and legal numbering.
- Quote acceptance is not a payment or recognized revenue event.

**Acceptance**
- Quote transitions and concurrent updates are tested.
- Totals and currency formatting are deterministic.
- Customer and admin views show the same quote state.

### Group C — Operations and finance

#### Stage 11 — Financial management, invoices, payments, and receivables
**Outcome:** auditable financial records and reconciled balances.

**Workflows**
- Issue invoice from an approved commercial event.
- Record payment, refund, adjustment, and allocation.
- Track due dates, partial payments, overdue status, and customer statement.
- Reconcile provider transactions where a payment provider exists.

**Data and APIs**
- Requires reviewed ledger/invoice/payment design before implementation.
- Use decimal money types, explicit currency, immutable posted entries, and idempotency keys.
- Keep quote, invoice, payment, and revenue semantics distinct.

**Acceptance**
- Ledger balances reconcile.
- Duplicate payment callbacks cannot double-post.
- Reversals use compensating entries; posted records are not silently overwritten.
- No financial KPI is shown until this stage is verified.

#### Stage 12 — Staff management
**Outcome:** staff directory, availability, skills, and operational profiles.

**Workflows**
- Create/update staff profile and specialization.
- Manage active status and availability.
- Assign staff to requests/tasks once the assignment workflow is available.
- Review workload based on recorded assignments and events.

**Data and APIs**
- Reuse User and StaffProfile.
- Do not infer performance from staff account count.
- Assignment and workload metrics require authoritative assignment records.

**Acceptance**
- Staff permissions are separate from customer permissions.
- Inactive staff cannot receive new assignments.
- Workload figures reconcile to assignments.

#### Stage 13 — Tasks and workflow management
**Outcome:** accountable operational work with traceable state.

**Workflows**
- Create tasks from requests or independently.
- Assign owner, due date, priority, checklist, and dependencies.
- Track status, blockers, comments, and completion evidence.
- Escalate overdue work under configured rules.

**Data and APIs**
- Requires task and workflow event models if no equivalent exists.
- Enforce valid transitions and assignment scope.
- Keep task completion separate from request completion.

**Acceptance**
- Task history is immutable/auditable.
- Due-date and escalation calculations respect timezone.
- Unauthorized assignment and cross-scope access fail.

#### Stage 14 — Communication and notifications
**Outcome:** dependable in-app and channel communication.

**Workflows**
- View notifications, mark read, filter, and open related records.
- Configure supported notification preferences.
- Track queued, sent, delivered, failed, and retried states when provider supports them.
- Manage templates in Arabic and English.

**Data and APIs**
- Reuse notification model/service where appropriate.
- Separate notification record creation from delivery attempt.
- Use retry/backoff and deduplication; never store bot tokens in notification rows.

**Acceptance**
- Failures and retries are visible to authorized operators.
- Duplicate events do not create duplicate customer messages.
- Delivery status is never inferred from an enqueue operation.

#### Stage 15 — Telegram bots, channels, groups, and destinations
**Outcome:** controlled Telegram integration operations.

**Workflows**
- Manage bot configuration references and destinations.
- Validate bot membership and posting capability.
- Route content/notifications to authorized destinations.
- Inspect webhook/polling status and safe error diagnostics.

**Data and APIs**
- Reuse current Telegram destination and runtime services.
- Secrets remain in environment/secret storage.
- Verify Telegram webhook secret and protect against replay.

**Acceptance**
- Unauthorized destination changes fail.
- Tokens and sensitive payloads are redacted.
- Telegram API failures are visible without exposing secrets.

### Group D — Content and automation

#### Stage 16 — Content management
**Outcome:** structured bilingual content lifecycle.

**Workflows**
- Create, edit, preview, review, publish-ready, archive content.
- Manage assets and metadata.
- Maintain Arabic/English variants and SEO fields where applicable.

**Data and APIs**
- Reuse content models.
- Sanitize rendered HTML/Markdown and validate media references.
- Keep draft content private.

**Acceptance**
- Drafts are not public.
- Content revisions and publishing changes are auditable.
- Locale fallback is explicit.

#### Stage 17 — Campaign management
**Outcome:** measurable, permission-controlled campaigns.

**Workflows**
- Create campaign, define audience and schedule, preview content, approve, pause, resume, and close.
- Track campaign outcomes only from recorded events.

**Data and APIs**
- Reuse campaign model where sufficient.
- Audience selection must honor consent, scope, and channel eligibility.
- Do not claim reach or conversion without event instrumentation.

**Acceptance**
- Campaign state transitions are tested.
- Audience exports are permission-scoped and audited.
- Metrics identify their source and attribution limits.

#### Stage 18 — Scheduling and publishing
**Outcome:** reliable scheduled publication and delivery tracking.

**Workflows**
- Schedule, reschedule, cancel, retry, and inspect publishing jobs.
- Preview destination-specific output.
- Review per-destination success/failure.

**Data and APIs**
- Reuse publishing contracts and worker boundaries.
- Use idempotency, bounded retries, and explicit timezone handling.
- Persist delivery attempts and provider response classifications.

**Acceptance**
- Duplicate worker execution does not duplicate publication.
- Cancelled jobs do not publish.
- Partial destination failures are represented accurately.

#### Stage 19 — AI assistant and controlled automation
**Outcome:** optional assistive automation with human oversight.

**Workflows**
- Suggest summaries, classifications, draft responses, and next actions.
- Require approval before external or irreversible actions.
- Allow operators to inspect input sources and output rationale.

**Data and APIs**
- Use provider-agnostic adapters and environment-backed credentials.
- No AI system may bypass RBAC, scope, audit, or workflow validation.
- No autonomous payment, account privilege, deletion, or publication action without explicit policy approval.

**Acceptance**
- Prompt injection and data leakage tests are included.
- AI output is labeled as generated and is not treated as authoritative source data.
- Human approval and audit are recorded for consequential actions.

### Group E — Governance and quality

#### Stage 20 — Analytics and reporting
**Outcome:** explainable reports with reproducible filters.

**Workflows**
- Build reports by period, service, status, channel, and organization when supported.
- Export authorized results.
- Drill down from aggregates to source records.

**Data and APIs**
- Every metric has a definition, owner, source query, timezone, and freshness policy.
- Use asynchronous/reporting projections only when query cost justifies them.
- Financial reports depend on verified ledger stage.

**Acceptance**
- Aggregates reconcile to source rows.
- Exports enforce the same filters and scopes as UI.
- Missing source data is shown as unavailable, never zero by assumption.

#### Stage 21 — Audit and governance
**Outcome:** searchable, trustworthy administrative history.

**Workflows**
- Search by actor, action, resource, and date.
- Inspect before/after changes where safe.
- Review privileged access and policy changes.
- Export records under strict permissions.

**Data and APIs**
- Reuse AuditLog and audit service.
- Avoid recording passwords, tokens, full private documents, or unnecessary personal data.
- Restrict mutation/deletion of audit records; use retention policy with legal review.

**Acceptance**
- Critical mutations create audit records in the same transaction or a reliable outbox.
- Audit search uses database pagination/count queries.
- Tampering and unauthorized access are tested.

#### Stage 22 — Security and risk management
**Outcome:** operational security controls and incident visibility.

**Workflows**
- Review login failures, suspicious access, permission changes, and integration errors.
- Manage supported security policies and session controls.
- Record incident triage and resolution.

**Data and APIs**
- Define threat model and security event taxonomy.
- Use rate limits, secure cookies/token lifecycle, CSRF protections where relevant, input validation, secret redaction, and dependency scanning.
- No security alert is displayed unless an actual event source exists.

**Acceptance**
- Authentication, authorization, session expiry, brute-force controls, and secret redaction have tests.
- Critical findings are tracked to resolution.
- No sensitive configuration is exposed through APIs or logs.

#### Stage 23 — System operations, QA, and production readiness
**Outcome:** observable, recoverable, tested platform operations.

**Workflows**
- Inspect health/readiness, background job state, database connectivity, storage and integration status.
- Review backups and restore verification evidence.
- Inspect error rates and release health.
- Execute release checklist and rollback plan.

**Data and APIs**
- Health checks must be based on real dependency probes and have bounded timeouts.
- Backup status requires actual backup artifacts and restore verification, not a placeholder row.
- Monitoring must avoid secrets and personal payloads.

**Acceptance**
- CI covers unit, integration, API authorization, migration, and frontend smoke tests.
- Backup restore is periodically verified in an isolated environment.
- Release is blocked by failed critical checks.
- Operational status distinguishes unknown, degraded, and healthy.

## 4. Dependency and delivery order

1. **Foundation/security first:** Stage 01 baseline, Stage 02, Stage 03, Stage 04.
2. **Organizational model:** Stage 05 only after scope ADR; it gates multi-organization data access.
3. **Core business operations:** Stages 06–10.
4. **Operational execution:** Stages 12–15, with Stage 13 assignment/workflow dependencies.
5. **Finance:** Stage 11 only after ledger design; do not fabricate balances before then.
6. **Content and automation:** Stages 16–19; AI actions remain approval-gated.
7. **Governance and readiness:** Stages 20–23, with security/audit requirements applied throughout.

Stages may be developed in parallel only when their domain contracts and schema dependencies are stable. A stage cannot be marked VERIFIED merely because its UI exists.

## 5. Initial repository findings to resolve in Phase 01

The following are concrete items observed in the current `main` snapshot and require targeted verification/fixes:
- RBAC role/permission administration currently uses the broad `admin:access` gate; a dedicated RBAC-management permission and safe bootstrap/migration strategy are required before opening role editing to more operators.
- Request update code contains direct Telegram HTTP delivery in the request handler; external delivery should move behind the notification/Telegram application service with retry and delivery tracking.
- Request update payloads and status transitions need typed validation and an explicit transition policy.
- Audit list total currently materializes matching IDs; replace with a database count query and test pagination behavior.
- Admin dashboard period filtering and drill-down contracts are not yet complete.
- The current model does not support staff assignment, branch scopes, or invoice/payment ledger; dependent KPIs remain BLOCKED.
- Existing legacy admin files/routes must remain until a verified replacement and deprecation plan exists.

These are findings from the remote GitHub snapshot, not a statement about an inaccessible local workspace.

## 6. Phase completion record

For each stage, maintain:
- scope and acceptance criteria;
- exact changed files and migrations;
- API and permission matrix;
- test cases and CI run;
- known limitations and source-data constraints;
- implementation status and verification evidence;
- rollback/deprecation notes where applicable.

No stage is complete until the above evidence is recorded.
