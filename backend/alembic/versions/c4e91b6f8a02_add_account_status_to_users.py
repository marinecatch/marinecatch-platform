"""Add account_status to users for real suspension enforcement

Revision ID: c4e91b6f8a02
Revises: 6e33c8b3fb53
Create Date: 2026-07-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c4e91b6f8a02'
down_revision: Union[str, None] = '6e33c8b3fb53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('account_status', sa.String(length=20), nullable=False, server_default='active'))


def downgrade() -> None:
    op.drop_column('users', 'account_status')