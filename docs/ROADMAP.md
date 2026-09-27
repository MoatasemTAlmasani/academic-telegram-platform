# Roadmap

## Completed

### Phase 0 — Project foundation

- Python/FastAPI entry point
- environment configuration
- logging and error handling
- health endpoint
- test and documentation foundation

### Phase 1 — Architecture and foundation

- modular domain boundaries
- API versioning
- readiness endpoint shape
- application service ports
- Telegram destination contracts
- publishing job contracts
- logging, security, and test architecture documentation

## Future phases

### Phase 2 — Core persistence

Introduce SQLAlchemy models, PostgreSQL sessions, Alembic migrations, and the
first domain persistence workflows.

### Phase 3 — Authentication and administration

Add authentication, authorization, RBAC, audit persistence, and the initial
admin API/dashboard foundation.

### Phase 4 — Telegram integration

Add aiogram transport, legitimate destination management, permission checks, and
validation logging.

### Phase 5 — Academic services and requests

Implement service catalog, customer requests, files, and quote workflows.

### Phase 6 — Publishing

Add content, campaigns, destination selection, queues, workers, scheduling,
publishing logs, and analytics.

No Phase 2+ functionality is implemented in this phase.