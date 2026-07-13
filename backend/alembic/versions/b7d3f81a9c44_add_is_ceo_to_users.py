"""Add is_ceo flag to users

Revision ID: b7d3f81a9c44
Revises: f2e8a710c9b3
Create Date: 2026-07-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b7d3f81a9c44'
down_revision: Union[str, None] = 'f2e8a710c9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('is_ceo', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_ceo')