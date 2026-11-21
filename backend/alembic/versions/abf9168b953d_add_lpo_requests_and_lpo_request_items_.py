"""Add lpo_requests and lpo_request_items tables

Revision ID: abf9168b953d
Revises: f1a2b3c4d5e6
Create Date: 2026-11-21 09:08:03.079978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abf9168b953d'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lpo_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('lpo_reference', sa.String(length=100), nullable=False),
        sa.Column('procurement_officer', sa.String(length=100), nullable=True),
        sa.Column('expected_fulfillment_date', sa.String(length=20), nullable=True),
        sa.Column('payment_terms_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lpo_requests_id', 'lpo_requests', ['id'])
    op.create_index('ix_lpo_requests_buyer_id', 'lpo_requests', ['buyer_id'])
    op.create_index('ix_lpo_requests_status', 'lpo_requests', ['status'])

    op.create_table(
        'lpo_request_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lpo_request_id', sa.Integer(), nullable=False),
        sa.Column('species', sa.String(length=50), nullable=False),
        sa.Column('quantity_kg', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('fulfilled_lot_id', sa.Integer(), nullable=True),
        sa.Column('resulting_order_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['lpo_request_id'], ['lpo_requests.id']),
        sa.ForeignKeyConstraint(['fulfilled_lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['resulting_order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lpo_request_items_id', 'lpo_request_items', ['id'])
    op.create_index('ix_lpo_request_items_lpo_request_id', 'lpo_request_items', ['lpo_request_id'])


def downgrade() -> None:
    op.drop_index('ix_lpo_request_items_lpo_request_id', table_name='lpo_request_items')
    op.drop_index('ix_lpo_request_items_id', table_name='lpo_request_items')
    op.drop_table('lpo_request_items')

    op.drop_index('ix_lpo_requests_status', table_name='lpo_requests')
    op.drop_index('ix_lpo_requests_buyer_id', table_name='lpo_requests')
    op.drop_index('ix_lpo_requests_id', table_name='lpo_requests')
    op.drop_table('lpo_requests')
