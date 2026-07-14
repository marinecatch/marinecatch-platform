"""Add logistics orchestration models — partners, storage nodes, cooler assets, transport jobs, custody events, exceptions

Revision ID: 6e33c8b3fb53
Revises: b7d3f81a9c44
Create Date: 2026-07-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6e33c8b3fb53'
down_revision: Union[str, Sequence[str], None] = 'b7d3f81a9c44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('logistics_partners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('partner_type', sa.String(length=30), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('coverage_areas', sa.Text(), nullable=True),
        sa.Column('cold_chain_capable', sa.Boolean(), nullable=True),
        sa.Column('max_payload_kg', sa.Float(), nullable=True),
        sa.Column('has_reefer', sa.Boolean(), nullable=True),
        sa.Column('temperature_range', sa.String(length=50), nullable=True),
        sa.Column('insurance_status', sa.String(length=30), nullable=True),
        sa.Column('export_certified', sa.Boolean(), nullable=True),
        sa.Column('has_api', sa.Boolean(), nullable=True),
        sa.Column('iot_compatible', sa.Boolean(), nullable=True),
        sa.Column('commission_model', sa.String(length=20), nullable=True),
        sa.Column('base_rate_kes', sa.Float(), nullable=True),
        sa.Column('per_km_rate_kes', sa.Float(), nullable=True),
        sa.Column('per_kg_rate_kes', sa.Float(), nullable=True),
        sa.Column('sla_pickup_hours', sa.Float(), nullable=True),
        sa.Column('sla_max_transit_hours', sa.Float(), nullable=True),
        sa.Column('on_time_rate', sa.Float(), nullable=True),
        sa.Column('dispute_rate', sa.Float(), nullable=True),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('total_jobs_completed', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('onboarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_logistics_partners_id', 'logistics_partners', ['id'])

    op.create_table('storage_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('operator_name', sa.String(length=150), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('county', sa.String(length=50), nullable=True),
        sa.Column('capacity_kg', sa.Float(), nullable=True),
        sa.Column('available_kg', sa.Float(), nullable=True),
        sa.Column('power_source', sa.String(length=20), nullable=True),
        sa.Column('has_backup_power', sa.Boolean(), nullable=True),
        sa.Column('has_ice_machine', sa.Boolean(), nullable=True),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('is_certified', sa.Boolean(), nullable=True),
        sa.Column('has_aluminium_shelves', sa.Boolean(), nullable=True),
        sa.Column('cost_model', sa.String(length=30), nullable=True),
        sa.Column('cost_rate_kes', sa.Float(), nullable=True),
        sa.Column('access_terms', sa.Text(), nullable=True),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('iot_sensor_id', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['logistics_partners.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_storage_nodes_id', 'storage_nodes', ['id'])

    op.create_table('cooler_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_code', sa.String(length=30), nullable=False),
        sa.Column('capacity_kg', sa.Float(), nullable=True),
        sa.Column('owner', sa.String(length=30), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('current_holder', sa.String(length=150), nullable=True),
        sa.Column('current_location', sa.String(length=150), nullable=True),
        sa.Column('iot_sensor_id', sa.String(length=50), nullable=True),
        sa.Column('purchase_value_kes', sa.Float(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('incident_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_code'),
    )
    op.create_index('ix_cooler_assets_id', 'cooler_assets', ['id'])
    op.create_index('ix_cooler_assets_asset_code', 'cooler_assets', ['asset_code'])

    op.create_table('transport_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('lot_id', sa.Integer(), nullable=True),
        sa.Column('pickup_location', sa.String(length=150), nullable=True),
        sa.Column('destination_location', sa.String(length=150), nullable=True),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('cooler_asset_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('scheduled_departure', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_departure', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cost_kes', sa.Float(), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('tracking_reference', sa.String(length=100), nullable=True),
        sa.Column('temperature_at_pickup', sa.Float(), nullable=True),
        sa.Column('temperature_at_delivery', sa.Float(), nullable=True),
        sa.Column('exception_notes', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['partner_id'], ['logistics_partners.id']),
        sa.ForeignKeyConstraint(['cooler_asset_id'], ['cooler_assets.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_transport_jobs_id', 'transport_jobs', ['id'])

    op.create_table('custody_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=True),
        sa.Column('transport_job_id', sa.Integer(), nullable=True),
        sa.Column('from_party', sa.String(length=150), nullable=True),
        sa.Column('to_party', sa.String(length=150), nullable=True),
        sa.Column('event_type', sa.String(length=30), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('recorded_by', sa.String(length=100), nullable=True),
        sa.Column('event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['transport_job_id'], ['transport_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_custody_events_id', 'custody_events', ['id'])

    op.create_table('logistics_exceptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transport_job_id', sa.Integer(), nullable=True),
        sa.Column('exception_type', sa.String(length=30), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resolution_status', sa.String(length=20), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reported_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['transport_job_id'], ['transport_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_logistics_exceptions_id', 'logistics_exceptions', ['id'])


def downgrade() -> None:
    op.drop_table('logistics_exceptions')
    op.drop_table('custody_events')
    op.drop_table('transport_jobs')
    op.drop_table('cooler_assets')
    op.drop_table('storage_nodes')
    op.drop_table('logistics_partners')