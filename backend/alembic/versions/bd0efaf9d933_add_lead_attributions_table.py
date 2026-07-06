"""Add lead_attributions table

Revision ID: bd0efaf9d933
Revises: 305f34d4a3c0
Create Date: 2026-07-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'bd0efaf9d933'
down_revision: Union[str, Sequence[str], None] = '305f34d4a3c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('lead_attributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('utm_term', sa.String(length=100), nullable=True),
        sa.Column('utm_content', sa.String(length=100), nullable=True),
        sa.Column('partner_code', sa.String(length=50), nullable=True),
        sa.Column('partner_campaign', sa.String(length=100), nullable=True),
        sa.Column('partner_referrer', sa.String(length=100), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('landing_page', sa.String(length=200), nullable=True),
        sa.Column('registration_source', sa.String(length=30), nullable=True),
        sa.Column('device', sa.String(length=30), nullable=True),
        sa.Column('browser', sa.String(length=50), nullable=True),
        sa.Column('os', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('lead_name', sa.String(length=100), nullable=True),
        sa.Column('lead_phone', sa.String(length=20), nullable=True),
        sa.Column('lead_email', sa.String(length=200), nullable=True),
        sa.Column('lead_role', sa.String(length=50), nullable=True),
        sa.Column('lead_location', sa.String(length=200), nullable=True),
        sa.Column('lead_message', sa.Text(), nullable=True),
        sa.Column('converted_to_user', sa.Boolean(), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_order_id', sa.Integer(), nullable=True),
        sa.Column('first_visit', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_visit', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['converted_order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lead_attributions_id', 'lead_attributions', ['id'])
    op.create_index('ix_lead_attributions_user_id', 'lead_attributions', ['user_id'])
    op.create_index('ix_lead_attributions_partner_code', 'lead_attributions', ['partner_code'])


def downgrade() -> None:
    op.drop_index('ix_lead_attributions_partner_code', table_name='lead_attributions')
    op.drop_index('ix_lead_attributions_user_id', table_name='lead_attributions')
    op.drop_index('ix_lead_attributions_id', table_name='lead_attributions')
    op.drop_table('lead_attributions')