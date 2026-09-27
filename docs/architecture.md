# Architecture direction

## Phase 0 boundaries

The project is organized around clear runtime boundaries:

- `backend/` — FastAPI HTTP application and cross-cutting concerns.
- `bot/` — future `aiogram` transport and Telegram handlers.
- `database/` — future SQLAlchemy models and Alembic migrations.
- `services/` — domain/application workflows independent of transport.
- `workers/` — future Redis-backed background jobs and scheduler processes.
- `configuration/` — configuration ownership notes and environment guidance.
- `tests/` — automated tests for the backend and future boundaries.
- `docs/` — product and engineering documentation.

The API currently exposes only a liveness check. Database, Redis, Telegram,
authentication, publishing, analytics, and admin dashboard behavior will be
introduced in later phases behind these boundaries.

## Security direction

Secrets and environment-specific values are loaded from environment variables.
The future Telegram destination system must only operate on groups or channels
where the bot has been legitimately added and has the required permissions.