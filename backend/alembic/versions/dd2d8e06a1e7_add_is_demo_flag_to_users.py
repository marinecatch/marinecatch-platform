"""Add is_demo flag to users

Revision ID: dd2d8e06a1e7
Revises: f9c2a4e78b31
Create Date: 2026-08-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'dd2d8e06a1e7'
down_revision: Union[str, Sequence[str], None] = 'f9c2a4e78b31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_demo')