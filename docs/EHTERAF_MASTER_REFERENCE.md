# EHTERAF Master Architecture Reference

**Status:** Approved architecture baseline  
**Repository:** `MoatasemTAlmasani/academic-telegram-platform`  
**Vercel project:** `academic-telegram-platform`  
**Domain:** `ehteraf-tech.vercel.app`

## 1. Five integrated systems

1. **Super Admin & Administration Dashboard** — platform governance and operations.
2. **Telegram Mini App** — customer experience inside Telegram.
3. **Telegram Bot** — conversations, service discovery, request assistance, notifications, support, and Telegram routing.
4. **Customer Portal** — customer account and service workspace on the web.
5. **Official Public Website** — company profile, service marketing, content, SEO, and public contact.

These are five experiences backed by shared central services and data, not five independent platforms or customer databases. Customer identity, profile, requests, and files must remain unified across Telegram Mini App and Customer Portal. Verified account linking must not create duplicate customers because a customer changes channel.

## 2. Approved decisions

| Decision | Approved value |
|---|---|
| Business model | **Hybrid** — EHTERAF operates the initial platform; prepare for future independent organizations without prematurely implementing full multi-tenancy |
| Languages | **Arabic and English** across all five systems |
| Direction | Full RTL/LTR |
| Visual direction | **Hybrid** — Premium Enterprise + Modern SaaS |
| Architecture | Continue the existing backend and favor a modular monolith until evidence justifies services |
| Identity | One central identity/customer record across channels |
| Notifications | No Firebase |
| Infrastructure | Preserve existing GitHub repository and Vercel project |

Hybrid readiness is not permission to create speculative tenant tables or migrations. Organization boundaries and data ownership require a documented design before implementation.

## 3. Shared platform capabilities

Identity/authentication; RBAC; customer profiles and channel linking; organization/future branch scope; service catalog; requests/workflows; file/document management; quotations; financial ledger/payment integrations when implemented; Telegram; notifications; content/campaigns/publishing; audit/observability/security/backup/recovery.

## 4. Administration workstream — 23 stages

### Group A — Foundation and control
1. Super Admin executive dashboard.
2. User and account management.
3. Roles and permissions (RBAC).
4. Platform-wide settings.
5. Organizations and branches.

### Group B — Customers, services, and requests
6. Service catalog management.
7. Customer management and identity linking.
8. Request management.
9. Files and document management.
10. Quotations management.

### Group C — Operations and finance
11. Financial management, invoices, payments, and receivables.
12. Staff management.
13. Tasks and workflow management.
14. Communication and notifications.
15. Telegram bots, channels, groups, and destinations.

### Group D — Content and automation
16. Content management.
17. Campaign management.
18. Scheduling and publishing.
19. AI assistant and controlled automation.

### Group E — Governance and quality
20. Analytics and reporting.
21. Audit and governance.
22. Security and risk management.
23. System operations, QA, and production readiness.

The roadmap is approved planning, not evidence of implementation.

## 5. Phase 01 — Super Admin & Administration Dashboard

### Objective
Improve the existing administration system in place. Preserve routes, APIs, models, and workflows unless a specific defect or justified architectural change is documented.

### Target capabilities
- Executive overview based on persisted, verified data.
- Customer, request, staff, and service KPIs.
- Request status and time-series analytics.
- Requests by service.
- Recent requests and administrative activity.
- Operational alerts for overdue requests and pending quotations.
- Functional navigation, backend-enforced access, Arabic/English, RTL/LTR, responsive layout, light/dark themes.
- Honest unavailable states for metrics whose source domains do not exist.

### Current model limitations
- Existing models include users, roles, permissions, staff profiles, services, requests, quotations, and audit logs.
- Requests are not assigned to staff in the current model.
- No invoice/payment ledger sufficient to calculate revenue or receivables was identified.
- Organization/branch data scopes were not identified.
- Do not fabricate revenue, balances, staff/branch performance, or system health.

### Implementation sequence
A. Correct authorization defects.  
B. Establish administration design system and shared layout.  
C. Improve navigation and responsive behavior without deleting existing pages.  
D. Implement executive dashboard from verified aggregates.  
E. Add analytics and operational queues only where source data exists.  
F. Add search, notifications, and preferences only with working backend contracts.  
G. Complete Arabic/English and RTL/LTR coverage.  
H. Run isolated tests, security checks, and document acceptance evidence.

## 6. Definition of done

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `PARTIAL`, `IMPLEMENTED`, `VERIFIED`, `BLOCKED`, `DEPRECATED`.

`IMPLEMENTED` means code exists. `VERIFIED` means behavior has been exercised by suitable tests/checks and evidence is recorded.

Every completed capability requires a documented workflow, backend validation/authorization, correct data scope, loading/empty/success/error states, risk-appropriate tests, localization, accessibility/responsiveness, and updated documentation.

## 7. Preservation and safety

- Continue the existing repository; do not create a replacement repository or Vercel project.
- Preserve user changes. Never reset, clean, stash, or discard them.
- Never delete existing pages, endpoints, or models without evidence and an approved migration plan.
- Never modify the production database or run production migrations during inspection/dashboard work.
- Use isolated test databases only.
- Do not change foundational technologies without an approved ADR.
- Do not introduce Firebase or fabricate business data.
- Do not commit, push, merge, deploy, or alter production configuration without explicit authorization.
- A remote branch cannot reveal uncommitted local Codespaces changes; reconcile local work before merging.

## 8. Phase 01 implementation baseline

The current admin frontend is served from `backend/app/static/admin`. Reuse existing backend routes and models. The RBAC data model is database-backed while Python role constants also exist; avoid competing authorization sources.

Request routes were observed using service-read permission constants for request operations. Use the existing request-specific read/update permissions instead. Financial and branch analytics remain unavailable until authoritative domain records and access scopes exist.

## 9. Change log

- **2026-11-06:** Approved five-system architecture, Hybrid business model, Arabic/English, Hybrid visual direction, and the 23-stage administration roadmap. Phase 01 authorized for controlled continuation on a feature branch.
