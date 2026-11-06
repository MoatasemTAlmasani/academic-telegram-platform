"""Add user preferences and account lock/expiry controls."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "dd44ee55ff66"
down_revision: Union[str, Sequence[str], None] = "cc33dd44ee55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("account_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("preferences", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("users", "preferences")
    op.drop_column("users", "account_expires_at")
    op.drop_column("users", "locked_until")
