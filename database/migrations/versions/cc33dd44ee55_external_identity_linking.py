"""Add verified external identities and one-time linking challenges."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cc33dd44ee55"
down_revision: Union[str, Sequence[str], None] = "bb22cc33dd44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "external_identities",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "linked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE",
            name="fk_external_identities_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_external_identities"),
        sa.UniqueConstraint(
            "provider", "subject", name="uq_external_identity_provider_subject"
        ),
        sa.UniqueConstraint(
            "user_id", "provider", name="uq_external_identity_user_provider"
        ),
    )
    op.create_index(
        "ix_external_identities_user_id",
        "external_identities",
        ["user_id"],
    )

    op.create_table(
        "identity_link_challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE",
            name="fk_identity_link_challenges_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_identity_link_challenges"),
        sa.UniqueConstraint("token_hash", name="uq_identity_link_challenges_token_hash"),
    )
    op.create_index(
        "ix_identity_link_challenges_user_id",
        "identity_link_challenges",
        ["user_id"],
    )
    op.create_index(
        "ix_identity_link_challenges_expires_at",
        "identity_link_challenges",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_link_challenges_expires_at",
        table_name="identity_link_challenges",
    )
    op.drop_index(
        "ix_identity_link_challenges_user_id",
        table_name="identity_link_challenges",
    )
    op.drop_table("identity_link_challenges")
    op.drop_index("ix_external_identities_user_id", table_name="external_identities")
    op.drop_table("external_identities")
