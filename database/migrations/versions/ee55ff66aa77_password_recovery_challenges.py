"""Add rate-limited, single-use password recovery challenges."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ee55ff66aa77"
down_revision: Union[str, Sequence[str], None] = "dd44ee55ff66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_recovery_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("identifier_key", sa.String(length=64), nullable=False),
        sa.Column("ip_key", sa.String(length=64), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_recovery_attempts_identifier_time", "password_recovery_attempts", ["identifier_key", "attempted_at"])
    op.create_index("ix_password_recovery_attempts_ip_time", "password_recovery_attempts", ["ip_key", "attempted_at"])
    op.create_index("ix_password_recovery_attempts_attempted_at", "password_recovery_attempts", ["attempted_at"])

    op.create_table(
        "password_recovery_challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("delivery_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_recovery_challenges_user_id", "password_recovery_challenges", ["user_id"])
    op.create_index("ix_password_recovery_challenges_expires_at", "password_recovery_challenges", ["expires_at"])
    op.create_index("ix_password_recovery_challenges_delivery_status", "password_recovery_challenges", ["delivery_status"])


def downgrade() -> None:
    op.drop_index("ix_password_recovery_challenges_delivery_status", table_name="password_recovery_challenges")
    op.drop_index("ix_password_recovery_challenges_expires_at", table_name="password_recovery_challenges")
    op.drop_index("ix_password_recovery_challenges_user_id", table_name="password_recovery_challenges")
    op.drop_table("password_recovery_challenges")
    op.drop_index("ix_password_recovery_attempts_attempted_at", table_name="password_recovery_attempts")
    op.drop_index("ix_password_recovery_attempts_ip_time", table_name="password_recovery_attempts")
    op.drop_index("ix_password_recovery_attempts_identifier_time", table_name="password_recovery_attempts")
    op.drop_table("password_recovery_attempts")
