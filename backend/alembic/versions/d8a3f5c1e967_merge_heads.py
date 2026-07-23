"""Merge heads: newsletter subscribers + account_status

Revision ID: d8a3f5c1e967
Revises: 2393888bdb20, c4e91b6f8a02
Create Date: 2026-07-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd8a3f5c1e967'
down_revision: Union[str, Sequence[str], None] = ('2393888bdb20', 'c4e91b6f8a02')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op — merges two independent branches (newsletter_subscribers table,
    # users.account_status column) back into a single head. No schema changes here.
    pass


def downgrade() -> None:
    pass