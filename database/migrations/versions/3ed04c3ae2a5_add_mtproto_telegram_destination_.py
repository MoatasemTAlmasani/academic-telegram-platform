"""add mtproto telegram destination statuses

Revision ID: 3ed04c3ae2a5
Revises: fe0613e23211
Create Date: 2026-10-05 19:21:16.501710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ed04c3ae2a5'
down_revision: Union[str, Sequence[str], None] = 'fe0613e23211'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add MTProto destination lifecycle statuses."""
    op.execute("""
        ALTER TYPE telegramvalidationstatus
        ADD VALUE IF NOT EXISTS 'IMPORTED'
    """)
    op.execute("""
        ALTER TYPE telegramvalidationstatus
        ADD VALUE IF NOT EXISTS 'JOINING'
    """)
    op.execute("""
        ALTER TYPE telegramvalidationstatus
        ADD VALUE IF NOT EXISTS 'JOINED'
    """)
    op.execute("""
        ALTER TYPE telegramvalidationstatus
        ADD VALUE IF NOT EXISTS 'JOIN_REQUEST_PENDING'
    """)
    op.execute("""
        ALTER TYPE telegramvalidationstatus
        ADD VALUE IF NOT EXISTS 'JOIN_FAILED'
    """)


def downgrade() -> None:
    """PostgreSQL enum values cannot be removed safely in-place."""
    pass
