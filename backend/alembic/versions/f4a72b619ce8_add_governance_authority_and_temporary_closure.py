"""Add governance_authority to AdminGeography and TemporaryClosure table

Revision ID: f4a72b619ce8
Revises: e91a4c082f13
Create Date: 2026-08-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f4a72b619ce8'
down_revision: Union[str, None] = 'e91a4c082f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('admin_geography', sa.Column('governance_authority', sa.String(length=200), nullable=True))

    op.create_table('temporary_closures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('landing_site_id', sa.Integer(), nullable=True),
        sa.Column('fishing_ground_id', sa.Integer(), nullable=True),
        sa.Column('closure_type', sa.String(length=50), nullable=True),
        sa.Column('target_species', sa.String(length=200), nullable=True),
        sa.Column('opens_date', sa.Date(), nullable=True),
        sa.Column('closes_date', sa.Date(), nullable=True),
        sa.Column('is_recurring', sa.String(length=10), nullable=True),
        sa.Column('governing_body', sa.String(length=200), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('source_year', sa.Integer(), nullable=True),
        sa.Column('source_page', sa.String(length=50), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=30), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['landing_site_id'], ['fish_landing_sites.id']),
        sa.ForeignKeyConstraint(['fishing_ground_id'], ['fishing_grounds.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('temporary_closures')
    op.drop_column('admin_geography', 'governance_authority')