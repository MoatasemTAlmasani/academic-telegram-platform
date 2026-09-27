# Infrastructure adapters

Adapters will implement the interfaces in `backend/app/application/ports.py`.
FastAPI routes, Telegram handlers, and domain modules should depend on those
interfaces rather than importing database, Redis, storage, or Telegram clients
directly.

Phase 1 intentionally provides contracts only. No external service is
connected.