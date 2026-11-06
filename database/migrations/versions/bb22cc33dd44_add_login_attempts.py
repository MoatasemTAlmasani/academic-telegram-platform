"""Add indexed login-attempt records for database-backed throttling."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bb22cc33dd44"
down_revision: Union[str, Sequence[str], None] = "aa11bb22cc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("username_key", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL",
            name="fk_login_attempts_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_login_attempts"),
    )
    op.create_index(
        "ix_login_attempts_username_time",
        "login_attempts",
        ["username_key", "attempted_at"],
    )
    op.create_index(
        "ix_login_attempts_ip_time",
        "login_attempts",
        ["ip_address", "attempted_at"],
    )
    op.create_index(
        "ix_login_attempts_attempted_at",
        "login_attempts",
        ["attempted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_login_attempts_attempted_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip_time", table_name="login_attempts")
    op.drop_index("ix_login_attempts_username_time", table_name="login_attempts")
    op.drop_table("login_attempts")
