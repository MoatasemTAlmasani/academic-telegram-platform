# Telegram Academic Services Platform

Phase 0 foundation for a Telegram-based academic and student services platform.

## Run & Operate

- `uv sync` — install Python dependencies
- `uv run python -m backend` — run the FastAPI server (port `8000`, or `PORT`)
- `uv run pytest` — run the Python test suite
- `curl http://localhost:8000/health` — verify the health endpoint
- `pnpm run typecheck` — typecheck the generated workspace support packages

Copy `.env.example` to `.env` for local development. Phase 0 does not require
external services or credentials.

## Stack

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic Settings for environment-backed configuration
- pytest and HTTPX for API tests
- PostgreSQL, SQLAlchemy, Alembic, Redis, aiogram, workers, and the future
  React/TypeScript dashboard are planned boundaries, not Phase 0 features.

## Where things live

- `backend/` — FastAPI application, settings, logging, errors, and routes
- `bot/` — reserved Telegram bot boundary
- `database/` — reserved PostgreSQL and migration boundary
- `services/` — reserved domain service boundary
- `workers/` — reserved background worker boundary
- `configuration/` — configuration ownership notes
- `tests/` — Python tests
- `docs/` — architecture and development documentation

## Architecture decisions

- Phase 0 keeps external services optional so the liveness endpoint works in a
  clean environment.
- Settings are loaded from environment variables and cached per process.
- HTTP error handling is centralized so future routes share the same safe
  response shape.
- The generated TypeScript workspace artifacts remain available as support
  tooling, but the platform foundation is implemented in Python/FastAPI.

## Product

The eventual product will support academic and student services through
Telegram, with an API, persistent data, background work, publishing, and an
administrative dashboard. Phase 0 only establishes the foundation.

## User preferences

No additional preferences recorded.

## Gotchas

- Do not add Telegram business logic, publishing, scheduling, dashboard
  features, or fake credentials before Phase 0 is approved.
- Use `uv sync` to keep `pyproject.toml` and `uv.lock` aligned.

## Pointers

- `docs/architecture.md` — boundary and security direction
- `docs/development.md` — setup, run, test, and health-check commands
- `docs/environment.md` — environment variable reference
