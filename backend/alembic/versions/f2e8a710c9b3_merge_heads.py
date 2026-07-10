"""Merge heads: lead pipeline fields + inventory processing fields

Revision ID: f2e8a710c9b3
Revises: 37c158e3005d, a1f4c9e02b77
Create Date: 2026-07-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f2e8a710c9b3'
down_revision: Union[str, Sequence[str], None] = ('37c158e3005d', 'a1f4c9e02b77')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op — this migration only merges two independent branches
    # (lead pipeline fields on users, processing fields on inventory_lots)
    # back into a single head. No schema changes here.
    pass


def downgrade() -> None:
    pass