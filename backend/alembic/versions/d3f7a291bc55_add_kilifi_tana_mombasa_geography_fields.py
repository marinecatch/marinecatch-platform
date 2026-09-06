"""Add Kilifi/Tana River/Mombasa geography fields — site role, environment type, node functions, confidence score, corridor status, ecological zones, landing baselines

Revision ID: d3f7a291bc55
Revises: c8b2e5f14a97
Create Date: 2026-08-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd3f7a291bc55'
down_revision: Union[str, None] = 'c8b2e5f14a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # FishLandingSite additions
    op.add_column('fish_landing_sites',
        sa.Column('site_role', sa.String(length=20), nullable=True))
    op.add_column('fish_landing_sites',
        sa.Column('aggregates_to_site_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_landing_site_aggregates_to', 'fish_landing_sites',
        'fish_landing_sites', ['aggregates_to_site_id'], ['id'])
    op.add_column('fish_landing_sites',
        sa.Column('environment_type', sa.String(length=20), nullable=True))
    op.add_column('fish_landing_sites',
        sa.Column('node_functions', sa.String(length=300), nullable=True))

    # ProvenanceMixin confidence_score — add to every table that uses the mixin
    provenance_tables = [
        'admin_geography', 'bmus', 'fish_landing_sites', 'fishing_grounds',
        'jcm_as', 'marine_management_areas', 'infrastructure_assets',
        'cold_chain_assets', 'logistics_nodes', 'supply_corridors',
        'species_availability', 'species_seasonality', 'markets', 'fishing_gears',
    ]
    for t in provenance_tables:
        op.add_column(t, sa.Column('confidence_score', sa.Integer(), nullable=True))

    # SupplyCorridor status — replace boolean-as-string with proper status
    op.add_column('supply_corridors',
        sa.Column('status', sa.String(length=20), nullable=True))
    op.execute("UPDATE supply_corridors SET status = 'potential' WHERE is_validated = 'false' OR is_validated IS NULL")
    op.execute("UPDATE supply_corridors SET status = 'validated' WHERE is_validated = 'true'")
    op.drop_column('supply_corridors', 'is_validated')

    # New table: EcologicalZone
    op.create_table('ecological_zones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('zone_type', sa.String(length=50), nullable=True),  # seagrass | mangrove | reef | turtle_foraging | mpa | creek
        sa.Column('landing_site_id', sa.Integer(), nullable=True),
        sa.Column('fishing_ground_id', sa.Integer(), nullable=True),
        sa.Column('protection_status', sa.String(length=50), nullable=True),
        sa.Column('area_km2', sa.Float(), nullable=True),
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

    # New table: CountyLandingBaseline
    op.create_table('county_landing_baselines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_geography_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_tonnes', sa.Float(), nullable=True),
        sa.Column('total_value_kes', sa.Float(), nullable=True),
        sa.Column('demersal_tonnes', sa.Float(), nullable=True),
        sa.Column('pelagic_tonnes', sa.Float(), nullable=True),
        sa.Column('shark_ray_tonnes', sa.Float(), nullable=True),
        sa.Column('crustacean_tonnes', sa.Float(), nullable=True),
        sa.Column('misc_tonnes', sa.Float(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('verification_status', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['admin_geography_id'], ['admin_geography.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('county_landing_baselines')
    op.drop_table('ecological_zones')
    op.add_column('supply_corridors', sa.Column('is_validated', sa.String(length=10), nullable=True))
    op.execute("UPDATE supply_corridors SET is_validated = 'true' WHERE status = 'validated'")
    op.execute("UPDATE supply_corridors SET is_validated = 'false' WHERE status != 'validated' OR status IS NULL")
    op.drop_column('supply_corridors', 'status')

    provenance_tables = [
        'admin_geography', 'bmus', 'fish_landing_sites', 'fishing_grounds',
        'jcm_as', 'marine_management_areas', 'infrastructure_assets',
        'cold_chain_assets', 'logistics_nodes', 'supply_corridors',
        'species_availability', 'species_seasonality', 'markets', 'fishing_gears',
    ]
    for t in provenance_tables:
        op.drop_column(t, 'confidence_score')

    op.drop_column('fish_landing_sites', 'node_functions')
    op.drop_column('fish_landing_sites', 'environment_type')
    op.drop_constraint('fk_landing_site_aggregates_to', 'fish_landing_sites', type_='foreignkey')
    op.drop_column('fish_landing_sites', 'aggregates_to_site_id')
    op.drop_column('fish_landing_sites', 'site_role')