"""Add catch_drafts table

Revision ID: 305f34d4a3c0
Revises: a3c3da9d3408
Create Date: 2026-07-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '305f34d4a3c0'
down_revision: Union[str, Sequence[str], None] = 'a3c3da9d3408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('catch_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(length=30), nullable=False),
        sa.Column('fisher_id', sa.Integer(), nullable=False),
        sa.Column('fisher_name', sa.String(length=100), nullable=True),
        sa.Column('fisher_phone', sa.String(length=20), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('member_id', sa.String(length=20), nullable=True),
        sa.Column('species', sa.String(length=50), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('landing_site', sa.String(length=100), nullable=True),
        sa.Column('catch_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gear_type', sa.String(length=50), nullable=True),
        sa.Column('vessel_registration', sa.String(length=50), nullable=True),
        sa.Column('asking_price_per_kg', sa.Float(), nullable=True),
        sa.Column('submission_channel', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True),
        sa.Column('quality_grade', sa.String(length=2), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('inspected_by', sa.String(length=100), nullable=True),
        sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_inventory_lot_id', sa.Integer(), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['fisher_clusters.id']),
        sa.ForeignKeyConstraint(['created_inventory_lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['fisher_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_number'),
    )
    op.create_index('ix_catch_drafts_id', 'catch_drafts', ['id'])
    op.create_index('ix_catch_drafts_reference_number', 'catch_drafts', ['reference_number'])


def downgrade() -> None:
    op.drop_index('ix_catch_drafts_reference_number', table_name='catch_drafts')
    op.drop_index('ix_catch_drafts_id', table_name='catch_drafts')
    op.drop_table('catch_drafts')