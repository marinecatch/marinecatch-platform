"""Add processing fields to inventory_lots

Revision ID: a1f4c9e02b77
Revises: bd0efaf9d933
Create Date: 2026-07-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1f4c9e02b77'
down_revision: Union[str, None] = 'bd0efaf9d933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reuse the existing 'productform' enum type — do NOT create a new one.
    processed_form_type = postgresql.ENUM(
        'whole_ungutted', 'whole_gutted', 'headed_gutted',
        'fillet', 'dried', 'smoked', 'live', 'other',
        name='productform',
        create_type=False
    )

    op.add_column('inventory_lots',
        sa.Column('processed_form', processed_form_type, nullable=True))
    op.add_column('inventory_lots',
        sa.Column('processed_weight_kg', sa.Float(), nullable=True))
    op.add_column('inventory_lots',
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('inventory_lots',
        sa.Column('processing_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('inventory_lots', 'processing_notes')
    op.drop_column('inventory_lots', 'processed_at')
    op.drop_column('inventory_lots', 'processed_weight_kg')
    op.drop_column('inventory_lots', 'processed_form')