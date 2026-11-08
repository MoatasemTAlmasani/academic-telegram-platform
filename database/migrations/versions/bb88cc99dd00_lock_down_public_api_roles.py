"""Lock the public PostgREST schema to server-side database access.

Revision ID: bb88cc99dd00
Revises: aa77bb88cc99

The application accesses PostgreSQL through its server-side SQLAlchemy
connection. It does not use Supabase's browser SDK or public Data API.
Therefore anon/authenticated receive no direct privileges on public objects;
RLS also denies those API roles while permitting existing server DB roles.
"""

from __future__ import annotations

from alembic import op

revision = "bb88cc99dd00"
down_revision = "aa77bb88cc99"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable and FORCE RLS on every current ordinary/partitioned table in public.
    # The policy only permits server-side DB roles; PostgREST's anon and
    # authenticated roles remain denied even if a table grant is re-added.
    op.execute(
        """
        DO $$
        DECLARE
            target record;
        BEGIN
            FOR target IN
                SELECT namespace.nspname AS schema_name,
                       relation.relname AS table_name,
                       relation.relrowsecurity AS rls_enabled
                FROM pg_class AS relation
                JOIN pg_namespace AS namespace
                  ON namespace.oid = relation.relnamespace
                WHERE namespace.nspname = 'public'
                  AND relation.relkind IN ('r', 'p')
            LOOP
                IF NOT target.rls_enabled THEN
                    EXECUTE format(
                        'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
                        target.schema_name,
                        target.table_name
                    );
                END IF;
                EXECUTE format(
                    'ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY',
                    target.schema_name,
                    target.table_name
                );
                EXECUTE format(
                    'CREATE POLICY %I ON %I.%I FOR ALL TO PUBLIC '
                    'USING (current_user NOT IN (''anon'', ''authenticated'')) '
                    'WITH CHECK (current_user NOT IN (''anon'', ''authenticated''))',
                    'server_side_access_bb88cc99dd00',
                    target.schema_name,
                    target.table_name
                );
            END LOOP;
        END
        $$;
        """
    )

    # RLS does not protect TRUNCATE, REFERENCES, or TRIGGER privileges.
    # Remove all direct access from the public API roles on existing objects.
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public "
        "FROM anon, authenticated"
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public "
        "FROM anon, authenticated"
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public "
        "FROM anon, authenticated"
    )

    # Supabase's current default ACL grants broad privileges to anon and
    # authenticated for objects created by postgres. Prevent the same exposure
    # from silently returning when future application migrations create objects.
    # The Supabase-managed supabase_admin owner also has broad default ACLs,
    # but the postgres migration role is not a member of supabase_admin and
    # PostgreSQL does not permit changing another role's default ACL. Current
    # objects are still revoked above; application migrations must continue to
    # create objects as postgres (the configured application migration owner).
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE ALL PRIVILEGES ON TABLES FROM anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE ALL PRIVILEGES ON SEQUENCES FROM anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated"
    )


def downgrade() -> None:
    # Reversing this migration would re-expose sensitive public tables and
    # restore broad default grants. Require a separately reviewed replacement
    # migration with explicit least-privilege policies instead.
    raise RuntimeError(
        "This security hardening migration is intentionally irreversible; "
        "do not restore public API access through an automatic downgrade."
    )
