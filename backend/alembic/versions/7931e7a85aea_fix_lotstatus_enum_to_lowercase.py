"""Fix lotstatus enum to lowercase

Revision ID: 7931e7a85aea
Revises: 580ffe3afa1f
Create Date: 2026-05-13 14:24:40.220655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7931e7a85aea'
down_revision: Union[str, Sequence[str], None] = '580ffe3afa1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE lotstatus RENAME TO lotstatus_old")
    op.execute("""
        CREATE TYPE lotstatus AS ENUM (
            'available',
            'reserved',
            'partially_sold',
            'sold',
            'in_transit',
            'delivered',
            'completed',
            'expired',
            'spoiled',
            'rejected'
        )
    """)
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN lot_status DROP DEFAULT,
            ALTER COLUMN lot_status TYPE lotstatus
            USING CASE lot_status::text
                WHEN 'AVAILABLE'     THEN 'available'::lotstatus
                WHEN 'RESERVED'      THEN 'reserved'::lotstatus
                WHEN 'PARTIALLY_SOLD' THEN 'partially_sold'::lotstatus
                WHEN 'SOLD'          THEN 'sold'::lotstatus
                WHEN 'IN_TRANSIT'    THEN 'in_transit'::lotstatus
                WHEN 'DELIVERED'     THEN 'delivered'::lotstatus
                WHEN 'COMPLETED'     THEN 'completed'::lotstatus
                WHEN 'EXPIRED'       THEN 'expired'::lotstatus
                WHEN 'SPOILED'       THEN 'spoiled'::lotstatus
                WHEN 'REJECTED'      THEN 'rejected'::lotstatus
                ELSE 'available'::lotstatus
            END,
            ALTER COLUMN lot_status SET DEFAULT 'available'::lotstatus
    """)
    op.execute("DROP TYPE lotstatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE lotstatus RENAME TO lotstatus_new")
    op.execute("""
        CREATE TYPE lotstatus AS ENUM (
            'AVAILABLE',
            'RESERVED',
            'PARTIALLY_SOLD',
            'SOLD',
            'IN_TRANSIT',
            'DELIVERED',
            'COMPLETED',
            'EXPIRED',
            'SPOILED',
            'REJECTED'
        )
    """)
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN lot_status DROP DEFAULT,
            ALTER COLUMN lot_status TYPE lotstatus
            USING CASE lot_status::text
                WHEN 'available'      THEN 'AVAILABLE'::lotstatus
                WHEN 'reserved'       THEN 'RESERVED'::lotstatus
                WHEN 'partially_sold' THEN 'PARTIALLY_SOLD'::lotstatus
                WHEN 'sold'           THEN 'SOLD'::lotstatus
                WHEN 'in_transit'     THEN 'IN_TRANSIT'::lotstatus
                WHEN 'delivered'      THEN 'DELIVERED'::lotstatus
                WHEN 'completed'      THEN 'COMPLETED'::lotstatus
                WHEN 'expired'        THEN 'EXPIRED'::lotstatus
                WHEN 'spoiled'        THEN 'SPOILED'::lotstatus
                WHEN 'rejected'       THEN 'REJECTED'::lotstatus
                ELSE 'AVAILABLE'::lotstatus
            END,
            ALTER COLUMN lot_status SET DEFAULT 'AVAILABLE'::lotstatus
    """)
    op.execute("DROP TYPE lotstatus_new")