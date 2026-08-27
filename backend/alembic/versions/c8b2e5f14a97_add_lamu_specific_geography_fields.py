"""Add Lamu-specific geography fields — land tenure, site classification, fishing gear

Revision ID: c8b2e5f14a97
Revises: a7e19c3d5f42
Create Date: 2026-08-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c8b2e5f14a97'
down_revision: Union[str, None] = 'a7e19c3d5f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fish_landing_sites',
        sa.Column('land_tenure_status', sa.String(length=30), nullable=True))
    op.add_column('fish_landing_sites',
        sa.Column('site_classification', sa.String(length=300), nullable=True))
    op.add_column('fish_landing_sites',
        sa.Column('is_island', sa.Boolean(), nullable=True))

    op.create_table('fishing_gears',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('local_name', sa.String(length=150), nullable=True),
        sa.Column('gear_category', sa.String(length=100), nullable=True),
        sa.Column('target_species', sa.String(length=300), nullable=True),
        sa.Column('prohibited_status', sa.String(length=30), nullable=True),
        sa.Column('selectivity_score', sa.Float(), nullable=True),
        sa.Column('environmental_risk', sa.String(length=30), nullable=True),
        sa.Column('permitted_area', sa.String(length=200), nullable=True),
        sa.Column('seasonality', sa.String(length=100), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('source_year', sa.Integer(), nullable=True),
        sa.Column('source_page', sa.String(length=50), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=30), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('fishing_gears')
    op.drop_column('fish_landing_sites', 'is_island')
    op.drop_column('fish_landing_sites', 'site_classification')
    op.drop_column('fish_landing_sites', 'land_tenure_status')