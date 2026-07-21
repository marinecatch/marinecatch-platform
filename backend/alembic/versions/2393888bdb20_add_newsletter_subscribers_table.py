"""Add newsletter_subscribers table

Revision ID: 2393888bdb20
Revises: 6e33c8b3fb53
Create Date: 2026-07-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2393888bdb20'
down_revision: Union[str, Sequence[str], None] = '6e33c8b3fb53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('newsletter_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('organization', sa.String(length=150), nullable=True),
        sa.Column('stakeholder_type', sa.String(length=30), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('consent', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('last_opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_newsletter_subscribers_id', 'newsletter_subscribers', ['id'])
    op.create_index('ix_newsletter_subscribers_email', 'newsletter_subscribers', ['email'])


def downgrade() -> None:
    op.drop_index('ix_newsletter_subscribers_email', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_id', table_name='newsletter_subscribers')
    op.drop_table('newsletter_subscribers')