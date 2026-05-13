"""Update OrderStatus enum with full lifecycle

Revision ID: 123c626dd002
Revises: 5db0873ce667
Create Date: 2026-05-13 10:38:16.625899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '123c626dd002'
down_revision: Union[str, Sequence[str], None] = '5db0873ce667'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE orderstatus RENAME TO orderstatus_old")
    op.execute("""
        CREATE TYPE orderstatus AS ENUM (
            'pending_payment',
            'paid',
            'confirmed',
            'preparing',
            'dispatched',
            'delivered',
            'completed',
            'cancelled',
            'payment_failed',
            'refunded'
        )
    """)
    op.execute("""
        ALTER TABLE orders
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE orderstatus
            USING CASE status::text
                WHEN 'pending'   THEN 'pending_payment'::orderstatus
                WHEN 'confirmed' THEN 'confirmed'::orderstatus
                WHEN 'dispatched' THEN 'dispatched'::orderstatus
                WHEN 'delivered' THEN 'delivered'::orderstatus
                WHEN 'cancelled' THEN 'cancelled'::orderstatus
                ELSE 'pending_payment'::orderstatus
            END,
            ALTER COLUMN status SET DEFAULT 'pending_payment'::orderstatus
    """)
    op.execute("DROP TYPE orderstatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE orderstatus RENAME TO orderstatus_new")
    op.execute("""
        CREATE TYPE orderstatus AS ENUM (
            'pending',
            'confirmed',
            'dispatched',
            'delivered',
            'cancelled'
        )
    """)
    op.execute("""
        ALTER TABLE orders
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE orderstatus
            USING CASE status::text
                WHEN 'pending_payment' THEN 'pending'::orderstatus
                WHEN 'paid'           THEN 'confirmed'::orderstatus
                WHEN 'confirmed'      THEN 'confirmed'::orderstatus
                WHEN 'preparing'      THEN 'confirmed'::orderstatus
                WHEN 'dispatched'     THEN 'dispatched'::orderstatus
                WHEN 'delivered'      THEN 'delivered'::orderstatus
                WHEN 'completed'      THEN 'delivered'::orderstatus
                WHEN 'cancelled'      THEN 'cancelled'::orderstatus
                ELSE 'pending'::orderstatus
            END,
            ALTER COLUMN status SET DEFAULT 'pending'::orderstatus
    """)
    op.execute("DROP TYPE orderstatus_new")