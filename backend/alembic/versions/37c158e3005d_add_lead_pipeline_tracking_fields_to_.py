"""Add lead pipeline tracking fields to User

Revision ID: 37c158e3005d
Revises: bd0efaf9d933
Create Date: 2026-07-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '37c158e3005d'
down_revision: Union[str, Sequence[str], None] = 'bd0efaf9d933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('lead_status', sa.String(), nullable=True))
    op.add_column('users', sa.Column('lead_source', sa.String(), nullable=True))
    op.add_column('users', sa.Column('assigned_to', sa.String(), nullable=True))
    op.add_column('users', sa.Column('lead_notes', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_contacted_at')
    op.drop_column('users', 'lead_notes')
    op.drop_column('users', 'assigned_to')
    op.drop_column('users', 'lead_source')
    op.drop_column('users', 'lead_status')