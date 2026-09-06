"""Extend Species with taxonomy/compliance fields and provenance; add habitat, gear, market price, processing profile tables

Revision ID: e91a4c082f13
Revises: d3f7a291bc55
Create Date: 2026-08-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e91a4c082f13'
down_revision: Union[str, None] = 'd3f7a291bc55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('species', sa.Column('order', sa.String(length=100), nullable=True))
    op.add_column('species', sa.Column('fao_code', sa.String(length=3), nullable=True))
    op.add_column('species', sa.Column('trophic_level', sa.Float(), nullable=True))
    op.add_column('species', sa.Column('max_size_cm', sa.Float(), nullable=True))
    op.add_column('species', sa.Column('cites_appendix', sa.String(length=10), nullable=True))
    op.add_column('species', sa.Column('eu_catch_cert_required', sa.Boolean(), nullable=True))
    op.add_column('species', sa.Column('iuu_risk_flag', sa.Boolean(), nullable=True))
    op.add_column('species', sa.Column('min_legal_size_cm', sa.Float(), nullable=True))
    op.add_column('species', sa.Column('size_limit_regulation_notes', sa.Text(), nullable=True))

    op.add_column('species', sa.Column('source_id', sa.Integer(), nullable=True))
    op.add_column('species', sa.Column('source_name', sa.String(length=255), nullable=True))
    op.add_column('species', sa.Column('source_year', sa.Integer(), nullable=True))
    op.add_column('species', sa.Column('source_page', sa.String(length=50), nullable=True))
    op.add_column('species', sa.Column('source_text', sa.Text(), nullable=True))
    op.add_column('species', sa.Column('verification_status', sa.String(length=30), nullable=True))
    op.execute("UPDATE species SET verification_status = 'RESEARCH_SOURCE' WHERE verification_status IS NULL")
    op.alter_column('species', 'verification_status', nullable=False)
    op.add_column('species', sa.Column('confidence_score', sa.Integer(), nullable=True))
    op.add_column('species', sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('species', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table('species_habitat_associations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('species_id', sa.Integer(), nullable=False),
        sa.Column('ecological_zone_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['species_id'], ['species.id']),
        sa.ForeignKeyConstraint(['ecological_zone_id'], ['ecological_zones.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('species_gear_associations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('species_id', sa.Integer(), nullable=False),
        sa.Column('fishing_gear_id', sa.Integer(), nullable=False),
        sa.Column('is_primary_target', sa.Boolean(), nullable=True),
        sa.Column('selectivity_score', sa.Float(), nullable=True),
        sa.Column('bycatch_risk', sa.String(length=20), nullable=True),
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
        sa.ForeignKeyConstraint(['species_id'], ['species.id']),
        sa.ForeignKeyConstraint(['fishing_gear_id'], ['fishing_gears.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('species_market_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('species_id', sa.Integer(), nullable=False),
        sa.Column('market_tier', sa.String(length=20), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('price_min', sa.Float(), nullable=True),
        sa.Column('price_max', sa.Float(), nullable=True),
        sa.Column('price_avg', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('observed_period', sa.String(length=50), nullable=True),
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
        sa.ForeignKeyConstraint(['species_id'], ['species.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('species_processing_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('species_id', sa.Integer(), nullable=False),
        sa.Column('product_form', sa.String(length=30), nullable=False),
        sa.Column('yield_percentage', sa.Float(), nullable=True),
        sa.Column('typical_loss_pct', sa.Float(), nullable=True),
        sa.Column('shelf_life_days_iced', sa.Float(), nullable=True),
        sa.Column('shelf_life_days_frozen', sa.Float(), nullable=True),
        sa.Column('handling_notes', sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(['species_id'], ['species.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('species_processing_profiles')
    op.drop_table('species_market_prices')
    op.drop_table('species_gear_associations')
    op.drop_table('species_habitat_associations')
    for col in ['updated_at', 'last_verified_at', 'confidence_score', 'verification_status',
                'source_text', 'source_page', 'source_year', 'source_name', 'source_id',
                'size_limit_regulation_notes', 'min_legal_size_cm', 'iuu_risk_flag',
                'eu_catch_cert_required', 'cites_appendix', 'max_size_cm', 'trophic_level',
                'fao_code', 'order']:
        op.drop_column('species', col)