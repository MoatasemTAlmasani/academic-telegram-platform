# Database

This boundary is reserved for PostgreSQL, SQLAlchemy 2.x models, and Alembic
migrations. No database connection or complete schema is required for Phase 1.

Future migrations should be kept in `database/migrations/` and applied through
an explicit deployment workflow. Application services should access the
database through infrastructure adapters instead of importing a session into
route handlers.