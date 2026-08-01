"""Add is_lead flag, decouple leads from is_active

Revision ID: f9c2a4e78b31
Revises: d8a3f5c1e967
Create Date: 2026-07-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f9c2a4e78b31'
down_revision: Union[str, None] = 'd8a3f5c1e967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('is_lead', sa.Boolean(), nullable=False, server_default='false'))

    # Data backfill: every existing row with is_active=False is a lead
    # (confirmed by full-codebase audit — this is the only place that
    # flag was ever set to False). Mark them as leads properly, and
    # restore is_active to True since it no longer carries lead-meaning.
    op.execute("""
        UPDATE users
        SET is_lead = TRUE, is_active = TRUE
        WHERE is_active = FALSE
    """)


def downgrade() -> None:
    # Not reversing the data backfill — restoring is_active=False for
    # former leads would recreate the exact collision this migration fixes.
    op.drop_column('users', 'is_lead')