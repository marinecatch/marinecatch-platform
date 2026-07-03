"""Add compliance_profiles and quality_inspections tables

Revision ID: a3c3da9d3408
Revises: 44c6252bac63
Create Date: 2026-06-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a3c3da9d3408'
down_revision: Union[str, Sequence[str], None] = '44c6252bac63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('compliance_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.String(length=20), nullable=True),
        sa.Column('compliance_level', sa.Integer(), nullable=True),
        sa.Column('national_id', sa.String(length=20), nullable=True),
        sa.Column('national_id_verified', sa.Boolean(), nullable=True),
        sa.Column('national_id_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('phone_verified', sa.Boolean(), nullable=True),
        sa.Column('phone_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('selfie_verified', sa.Boolean(), nullable=True),
        sa.Column('bmu_membership_number', sa.String(length=50), nullable=True),
        sa.Column('bmu_name', sa.String(length=100), nullable=True),
        sa.Column('bmu_verified', sa.Boolean(), nullable=True),
        sa.Column('bmu_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fisher_cluster_id', sa.Integer(), nullable=True),
        sa.Column('vessel_registration', sa.String(length=50), nullable=True),
        sa.Column('gear_type', sa.String(length=50), nullable=True),
        sa.Column('default_landing_site', sa.String(length=100), nullable=True),
        sa.Column('kra_pin', sa.String(length=20), nullable=True),
        sa.Column('kra_verified', sa.Boolean(), nullable=True),
        sa.Column('kra_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('business_registration_number', sa.String(length=50), nullable=True),
        sa.Column('business_type', sa.String(length=50), nullable=True),
        sa.Column('tax_status', sa.String(length=30), nullable=True),
        sa.Column('etims_enabled', sa.Boolean(), nullable=True),
        sa.Column('etims_enabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('buyer_tier', sa.Integer(), nullable=True),
        sa.Column('signed_agreement', sa.Boolean(), nullable=True),
        sa.Column('signed_agreement_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_certificate', sa.Boolean(), nullable=True),
        sa.Column('sustainability_certified', sa.Boolean(), nullable=True),
        sa.Column('export_permit', sa.Boolean(), nullable=True),
        sa.Column('export_markets', sa.String(length=200), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('delivery_reliability', sa.Float(), nullable=True),
        sa.Column('payment_score', sa.Float(), nullable=True),
        sa.Column('total_transactions', sa.Integer(), nullable=True),
        sa.Column('total_volume_kg', sa.Float(), nullable=True),
        sa.Column('total_value_kes', sa.Float(), nullable=True),
        sa.Column('rejection_rate', sa.Float(), nullable=True),
        sa.Column('on_time_delivery_rate', sa.Float(), nullable=True),
        sa.Column('months_active', sa.Integer(), nullable=True),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('first_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['fisher_cluster_id'], ['fisher_clusters.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_compliance_profiles_id', 'compliance_profiles', ['id'])
    op.create_index('ix_compliance_profiles_member_id', 'compliance_profiles', ['member_id'], unique=True)
    op.create_index('ix_compliance_profiles_user_id', 'compliance_profiles', ['user_id'], unique=True)

    op.create_table('quality_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=False),
        sa.Column('inspector_id', sa.Integer(), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True),
        sa.Column('grade', sa.String(length=2), nullable=True),
        sa.Column('disposition', sa.String(length=30), nullable=True),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('temperature_ok', sa.Boolean(), nullable=True),
        sa.Column('smell_ok', sa.Boolean(), nullable=True),
        sa.Column('texture_ok', sa.Boolean(), nullable=True),
        sa.Column('appearance_ok', sa.Boolean(), nullable=True),
        sa.Column('ice_ratio_ok', sa.Boolean(), nullable=True),
        sa.Column('gills_ok', sa.Boolean(), nullable=True),
        sa.Column('eyes_ok', sa.Boolean(), nullable=True),
        sa.Column('declared_weight_kg', sa.Float(), nullable=True),
        sa.Column('verified_weight_kg', sa.Float(), nullable=True),
        sa.Column('weight_variance_kg', sa.Float(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('conditions', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('photos_taken', sa.Boolean(), nullable=True),
        sa.Column('photo_urls', sa.Text(), nullable=True),
        sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id']),
        sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quality_inspections_id', 'quality_inspections', ['id'])
    op.create_index('ix_quality_inspections_lot_id', 'quality_inspections', ['lot_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_quality_inspections_lot_id', table_name='quality_inspections')
    op.drop_index('ix_quality_inspections_id', table_name='quality_inspections')
    op.drop_table('quality_inspections')
    op.drop_index('ix_compliance_profiles_user_id', table_name='compliance_profiles')
    op.drop_index('ix_compliance_profiles_member_id', table_name='compliance_profiles')
    op.drop_index('ix_compliance_profiles_id', table_name='compliance_profiles')
    op.drop_table('compliance_profiles')