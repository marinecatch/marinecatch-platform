"""Add optional age field to users

Revision ID: a7e19c3d5f42
Revises: 528324f9d589
Create Date: 2026-07-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a7e19c3d5f42'
down_revision: Union[str, None] = '528324f9d589'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('age', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'age')