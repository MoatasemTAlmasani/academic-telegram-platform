"""Store user last-seen timestamps with timezone awareness."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ff66aa77bb88"
down_revision: Union[str, Sequence[str], None] = "ee55ff66aa77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "last_seen_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="last_seen_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "last_seen_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="last_seen_at AT TIME ZONE 'UTC'",
    )
