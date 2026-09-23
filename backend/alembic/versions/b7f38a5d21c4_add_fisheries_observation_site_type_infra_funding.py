"""Add FisheriesObservation table, FishLandingSite.site_type, InfrastructureAsset funding fields

Revision ID: b7f38a5d21c4
Revises: a2c9d174e6f0
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b7f38a5d21c4'
down_revision: Union[str, None] = 'a2c9d174e6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fish_landing_sites', sa.Column('site_type', sa.String(length=30), nullable=True))

    op.add_column('infrastructure_assets', sa.Column('funding_program', sa.String(length=100), nullable=True))
    op.add_column('infrastructure_assets', sa.Column('financier', sa.String(length=150), nullable=True))
    op.add_column('infrastructure_assets', sa.Column('reported_value', sa.Float(), nullable=True))
    op.add_column('infrastructure_assets', sa.Column('reported_value_currency', sa.String(length=3), nullable=True))

    op.create_table('fisheries_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_geography_id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=40), nullable=False),
        sa.Column('metric_subtype', sa.String(length=50), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('period_year', sa.Integer(), nullable=True),
        sa.Column('period_month', sa.Integer(), nullable=True),
        sa.Column('frame_reference_year', sa.Integer(), nullable=True),
        sa.Column('is_canonical', sa.String(length=10), nullable=True),
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
        sa.ForeignKeyConstraint(['admin_geography_id'], ['admin_geography.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('fisheries_observations')
    op.drop_column('infrastructure_assets', 'reported_value_currency')
    op.drop_column('infrastructure_assets', 'reported_value')
    op.drop_column('infrastructure_assets', 'financier')
    op.drop_column('infrastructure_assets', 'funding_program')
    op.drop_column('fish_landing_sites', 'site_type')