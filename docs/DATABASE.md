# Database

PostgreSQL is the planned primary datastore. SQLAlchemy 2.x is the planned ORM
and Alembic is the planned migration tool.

Phase 1 does not create the complete schema, initialize a database session, or
run migrations. The `database/` boundary is reserved for:

- SQLAlchemy models organized by domain module
- session and transaction management
- Alembic migration history
- database-specific repositories and adapters
- integration tests

Database access should remain behind infrastructure interfaces so domain and
application code can be tested without a live PostgreSQL instance.