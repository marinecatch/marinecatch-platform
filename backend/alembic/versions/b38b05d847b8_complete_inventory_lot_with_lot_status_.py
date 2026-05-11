"""Complete inventory_lot with lot_status and missing columns

Revision ID: b38b05d847b8
Revises: ce34d312b8cf
Create Date: 2026-05-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b38b05d847b8'
down_revision: Union[str, None] = 'ce34d312b8cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first before adding column
    lotstatus = sa.Enum(
        'AVAILABLE', 'RESERVED', 'PARTIALLY_SOLD', 'SOLD',
        'IN_TRANSIT', 'DELIVERED', 'COMPLETED', 'EXPIRED',
        'SPOILED', 'REJECTED',
        name='lotstatus'
    )
    lotstatus.create(op.get_bind(), checkfirst=True)

    # Add missing columns
    op.add_column('inventory_lots',
        sa.Column('lot_status', lotstatus, nullable=True))
    op.add_column('inventory_lots',
        sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('inventory_lots',
        sa.Column('estimated_expiry', sa.DateTime(timezone=True), nullable=True))
    op.add_column('inventory_lots',
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True))
    op.add_column('inventory_lots',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # Set defaults before making not nullable
    op.execute("UPDATE inventory_lots SET lot_status = 'AVAILABLE' WHERE lot_status IS NULL")
    op.execute("UPDATE inventory_lots SET is_active = TRUE WHERE is_active IS NULL")

    # Now make them not nullable
    op.alter_column('inventory_lots', 'lot_status', nullable=False)
    op.alter_column('inventory_lots', 'is_active', nullable=False)

    # Add index
    op.create_index('ix_inventory_lots_lot_status', 'inventory_lots', ['lot_status'])


def downgrade() -> None:
    op.drop_index('ix_inventory_lots_lot_status', table_name='inventory_lots')
    op.drop_column('inventory_lots', 'updated_at')
    op.drop_column('inventory_lots', 'created_at')
    op.drop_column('inventory_lots', 'estimated_expiry')
    op.drop_column('inventory_lots', 'is_active')
    op.drop_column('inventory_lots', 'lot_status')
    sa.Enum(name='lotstatus').drop(op.get_bind(), checkfirst=True)