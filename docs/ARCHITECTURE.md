# Architecture

## Purpose

This project is the foundation for a Telegram-based academic and student
services platform. Phase 1 establishes boundaries and contracts without
implementing the complete product.

## System flow

```text
User
  ↓
Telegram Bot / Future Admin Dashboard
  ↓
FastAPI API (/api/v1)
  ↓
Application Services / Use Cases
  ↓
Domain Modules
  ↓
Infrastructure Adapters
  ↓
PostgreSQL / Redis / Telegram API / File Storage
```

## Layer responsibilities

- **API** — versioned HTTP routes, request validation, response contracts.
- **Application** — use-case orchestration and ports for infrastructure.
- **Domain** — capability-specific rules and contracts.
- **Infrastructure** — database, queue, Telegram, storage, and notification
  adapters.
- **External systems** — PostgreSQL, Redis, Telegram, and file storage.

Routes and Telegram handlers must delegate to application services. Business
logic should not be embedded in transport handlers.

## Domain boundaries

The planned modules are authentication, users, services, requests, files,
quotes, Telegram, campaigns, publishing, notifications, analytics, audit, and
administration. Each lives independently under `backend/app/modules/`.

## Phase 1 decisions

- `/api/v1` is the canonical API namespace; root health routes remain as
  compatibility and operational shortcuts.
- External services are represented by application ports and future adapters.
- PostgreSQL, Redis, and Telegram are not connected until their respective
  implementation phases.
- Telegram destination statuses and publishing job contracts are defined now,
  but validation, queueing, scheduling, and delivery are not implemented.
- The future React/TypeScript/Tailwind dashboard has a reserved foundation
  boundary in `frontend/`.