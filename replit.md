# Telegram Academic Services Platform

Phase 1 architecture and foundation for a Telegram-based academic and student
services platform.

## Run & Operate

- `uv sync --dev` — install Python dependencies
- `uv run python -m backend` — run the FastAPI server (port `8000`, or `PORT`)
- `uv run pytest` — run the Python test suite
- `curl http://localhost:8000/health` — verify the health endpoint
- `curl http://localhost:8000/health/ready` — verify readiness shape
- `pnpm run typecheck` — typecheck the generated workspace support packages

Copy `.env.example` to `.env` for local development. Phase 1 does not connect
to external services or require credentials.

## Stack

- Python 3.12+
- FastAPI and Uvicorn
- Pydantic Settings for environment-backed configuration
- pytest and HTTPX for API tests
- PostgreSQL, SQLAlchemy 2.x, Alembic, Redis, aiogram, background workers, and
  the future React/TypeScript/Tailwind dashboard are planned boundaries.

## Where things live

- `backend/app/api/` — versioned FastAPI routes
- `backend/app/application/` — use-case layer and service ports
- `backend/app/domain/` — transport-independent domain layer
- `backend/app/infrastructure/` — external service adapter boundary
- `backend/app/modules/` — independent business capability boundaries
- `bot/` — reserved Telegram bot transport boundary
- `database/` — reserved PostgreSQL and Alembic boundary
- `services/` — reserved domain service boundary
- `workers/` — reserved background worker boundary
- `frontend/` — reserved React/TypeScript/Tailwind dashboard boundary
- `tests/` — unit, integration, API, Telegram, database, and worker test areas
- `docs/` — architecture, API, database, Telegram, security, and roadmap docs

## Architecture decisions

- Phase 1 keeps external services optional so health and readiness checks work
  in a clean environment.
- Settings are loaded from environment variables and cached per process.
- HTTP error handling is centralized and versioned routes live under `/api/v1`.
- Application ports isolate future PostgreSQL, Redis, Telegram, storage, and
  notification adapters from route handlers and domain rules.
- Telegram and publishing contracts define future workflows without executing
  them.

## Product

The eventual product will support academic and student services through
Telegram, with an API, persistent data, background work, publishing, and an
administrative dashboard. Phase 1 establishes the architecture for those
future capabilities.

## User preferences

No additional preferences recorded.

## Gotchas

- Do not add complete Telegram business logic, bulk destination validation,
  publishing, scheduling, dashboard features, database schema, or fake
  credentials before the relevant phase is approved.
- Use `uv sync` to keep `pyproject.toml` and `uv.lock` aligned.

## Pointers

- `docs/ARCHITECTURE.md` — boundary and architecture decisions
- `docs/API.md` — versioning and response conventions
- `docs/DATABASE.md` — planned PostgreSQL/SQLAlchemy/Alembic boundary
- `docs/TELEGRAM.md` — Telegram and destination architecture
- `docs/SECURITY.md` — security foundation
- `docs/ROADMAP.md` — phased implementation plan
