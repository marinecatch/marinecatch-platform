"""Add Zanzibar governance layer — GoverningAuthority, ShehiaFisheriesCommittee, ManagementArea, generic TemporaryClosure, comanagement governance_type

Revision ID: a2c9d174e6f0
Revises: f4a72b619ce8
Create Date: 2026-08-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a2c9d174e6f0'
down_revision: Union[str, None] = 'f4a72b619ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the earlier single-purpose TemporaryClosure table from
    # f4a72b619ce8 and replace with the generic version — no data
    # exists in it yet (Zanzibar seed not yet run), safe to swap.
    op.drop_table('temporary_closures')

    op.create_table('governing_authorities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('jurisdiction', sa.String(length=50), nullable=False),
        sa.Column('country_code', sa.String(length=3), nullable=False),
        sa.Column('governance_type', sa.String(length=30), nullable=True),
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
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('shehia_fisheries_committees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('alternate_name', sa.String(length=200), nullable=True),
        sa.Column('shehia_id', sa.Integer(), nullable=True),
        sa.Column('formation_year', sa.Integer(), nullable=True),
        sa.Column('active_status', sa.String(length=30), nullable=True),
        sa.Column('cmg_affiliation_status', sa.String(length=30), nullable=True),
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
        sa.ForeignKeyConstraint(['shehia_id'], ['admin_geography.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_shehia_fisheries_committees_name', 'name')
    )

    op.create_table('management_areas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('marine_management_area_id', sa.Integer(), nullable=False),
        sa.Column('zone_number', sa.String(length=20), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
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
        sa.ForeignKeyConstraint(['marine_management_area_id'], ['marine_management_areas.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('management_area_sfc',
        sa.Column('management_area_id', sa.Integer(), nullable=False),
        sa.Column('sfc_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['management_area_id'], ['management_areas.id']),
        sa.ForeignKeyConstraint(['sfc_id'], ['shehia_fisheries_committees.id']),
        sa.PrimaryKeyConstraint('management_area_id', 'sfc_id')
    )

    op.create_table('sfc_jcma',
        sa.Column('sfc_id', sa.Integer(), nullable=False),
        sa.Column('jcma_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['sfc_id'], ['shehia_fisheries_committees.id']),
        sa.ForeignKeyConstraint(['jcma_id'], ['jcm_as.id']),
        sa.PrimaryKeyConstraint('sfc_id', 'jcma_id')
    )

    op.create_table('temporary_closures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('closure_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('reopen_date', sa.Date(), nullable=True),
        sa.Column('target_species_id', sa.Integer(), nullable=True),
        sa.Column('landing_site_id', sa.Integer(), nullable=True),
        sa.Column('fishing_ground_id', sa.Integer(), nullable=True),
        sa.Column('management_area_id', sa.Integer(), nullable=True),
        sa.Column('marine_management_area_id', sa.Integer(), nullable=True),
        sa.Column('governing_sfc_id', sa.Integer(), nullable=True),
        sa.Column('governing_cmg_id', sa.Integer(), nullable=True),
        sa.Column('geometry_note', sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(['target_species_id'], ['species.id']),
        sa.ForeignKeyConstraint(['landing_site_id'], ['fish_landing_sites.id']),
        sa.ForeignKeyConstraint(['fishing_ground_id'], ['fishing_grounds.id']),
        sa.ForeignKeyConstraint(['management_area_id'], ['management_areas.id']),
        sa.ForeignKeyConstraint(['marine_management_area_id'], ['marine_management_areas.id']),
        sa.ForeignKeyConstraint(['governing_sfc_id'], ['shehia_fisheries_committees.id']),
        sa.ForeignKeyConstraint(['governing_cmg_id'], ['jcm_as.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # FishLandingSite additions
    op.add_column('fish_landing_sites', sa.Column('sfc_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_landing_site_sfc', 'fish_landing_sites', 'shehia_fisheries_committees', ['sfc_id'], ['id'])
    op.add_column('fish_landing_sites', sa.Column('data_verification_stage', sa.String(length=30), nullable=True))
    op.add_column('fish_landing_sites', sa.Column('production_system', sa.String(length=20), nullable=True))

    # AdminGeography addition
    op.add_column('admin_geography', sa.Column('governing_authority_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_admin_geo_governing_authority', 'admin_geography', 'governing_authorities', ['governing_authority_id'], ['id'])

    # JointCoManagementArea addition
    op.add_column('jcm_as', sa.Column('governance_type', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('jcm_as', 'governance_type')
    op.drop_constraint('fk_admin_geo_governing_authority', 'admin_geography', type_='foreignkey')
    op.drop_column('admin_geography', 'governing_authority_id')
    op.drop_column('fish_landing_sites', 'production_system')
    op.drop_column('fish_landing_sites', 'data_verification_stage')
    op.drop_constraint('fk_landing_site_sfc', 'fish_landing_sites', type_='foreignkey')
    op.drop_column('fish_landing_sites', 'sfc_id')

    op.drop_table('temporary_closures')
    op.drop_table('sfc_jcma')
    op.drop_table('management_area_sfc')
    op.drop_table('management_areas')
    op.drop_table('shehia_fisheries_committees')
    op.drop_table('governing_authorities')

    # Recreate the earlier single-purpose temporary_closures table
    # to make downgrade symmetric with f4a72b619ce8
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