"""Persist Telegram worker state and request idempotency keys."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a29d806c12"
down_revision: Union[str, Sequence[str], None] = "3ed04c3ae2a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("telegram_update_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "uq_service_requests_telegram_update_id",
        "service_requests",
        ["telegram_update_id"],
        unique=True,
    )
    op.create_table(
        "telegram_conversation_states",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("chat_id", name="pk_telegram_conversation_states"),
    )
    op.create_table(
        "telegram_processed_updates",
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column("update_type", sa.String(length=80), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("update_id", name="pk_telegram_processed_updates"),
    )


def downgrade() -> None:
    op.drop_table("telegram_processed_updates")
    op.drop_table("telegram_conversation_states")
    op.drop_index(
        "uq_service_requests_telegram_update_id",
        table_name="service_requests",
    )
    op.drop_column("service_requests", "telegram_update_id")
