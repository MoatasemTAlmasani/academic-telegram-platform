# Database

This boundary is reserved for PostgreSQL, SQLAlchemy models, and Alembic
migrations. No database connection or schema is required for Phase 0.

Future migrations should be kept in `database/migrations/` and applied through
an explicit deployment workflow.