# EHTERAF Platform Architecture — Approved Reference

## Five integrated systems
1. Super Admin & Administration Dashboard.
2. Telegram Mini App.
3. Telegram Bot.
4. Customer Portal.
5. Official Public Website.

All five experiences share central identity, authorization, APIs, customer records, and operational data. A customer must retain one identity across Telegram Mini App and Customer Portal; channel identity is linked to the same customer account rather than creating duplicates.

## Approved decisions
- **Business model: HYBRID.** EHTERAF is the initial owner/operator. Prepare for future independent organizations without implementing full multi-tenancy prematurely.
- **Languages: Arabic + English** across all five systems, with correct RTL/LTR and localized dates, numbers, and currencies.
- **Visual direction: HYBRID**, combining Premium Enterprise and Modern SaaS; responsive, accessible, light and dark themes.
- Prefer a modular monolith and clear domain boundaries until there is a demonstrated reason to extract services.
- No Firebase. Never fabricate customers, testimonials, business metrics, revenue, or financial balances.

## Shared capabilities
Identity and account linking; RBAC and data scopes; customer profiles; service catalog; request lifecycle; files; quotations and future billing; staff and task workflows; Telegram integration; notifications; content and campaigns; audit; analytics; settings; monitoring.

## Administration Phase 01
The new administration console reuses the existing FastAPI application and APIs. The previous interface is retained at /admin/legacy; the new console is served at /admin.

Implemented scope in this delivery: existing JWT sign-in; authenticated access summary with real roles/permissions; persisted dashboard aggregates for customers, requests, services, staff, quotations and audit; customer/user, service, request, staff, RBAC, audit and application-settings screens; Arabic/English, RTL/LTR, light/dark, responsive layout. Revenue/receivables, branch performance and staff performance are explicitly unavailable until their underlying data models exist.

Navigation is only shown for implemented capabilities. A module is not considered operational until API, authorization, data source and tests exist.

## Future admin navigation roadmap
Dashboard; administration/users/roles; organization/companies/branches; staff; customers; services; operations/requests/tasks/workflows; documents; finance/quotations/invoices/payments; communication/notifications/messages; Telegram integrations; marketing/content/campaigns/publishing; analytics/reports; governance/audit; system settings/monitoring.

## Preservation and security
- Preserve existing working-tree modifications; never reset, clean, stash, or discard user changes.
- Never modify production databases or run migrations against production.
- Use isolated test databases only.
- Do not delete existing routes or functionality without proving obsolescence and obtaining approval.
- No foundational technology changes without an ADR and approval. No Firebase.
- No commit, push, deployment, or production-setting changes without explicit approval.
- Enforce authorization in backend dependencies; frontend filtering is not a security boundary.
- Never expose password hashes, tokens, or secrets to the browser.
- Financial values must originate from an invoice/payment/receivables ledger.

## Status vocabulary
NOT_STARTED, IN_PROGRESS, PARTIAL, IMPLEMENTED, VERIFIED, BLOCKED, DEPRECATED. Implemented is not verified.
