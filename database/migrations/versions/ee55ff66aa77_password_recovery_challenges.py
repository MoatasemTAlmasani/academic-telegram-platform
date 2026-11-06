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
        sa.Column("delivery_status", sa.String(length=20), nullable=FalmÆÈ‹j◊ù