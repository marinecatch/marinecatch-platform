"""Fix ordertype enum to lowercase

Revision ID: 580ffe3afa1f
Revises: 123c626dd002
Create Date: 2026-05-13 12:18:11.596725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '580ffe3afa1f'
down_revision: Union[str, Sequence[str], None] = '123c626dd002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE ordertype RENAME TO ordertype_old")
    op.execute("""
        CREATE TYPE ordertype AS ENUM (
            'marketplace',
            'procurement',
            'fulfillment'
        )
    """)
    op.execute("""
        ALTER TABLE orders
            ALTER COLUMN order_type DROP DEFAULT,
            ALTER COLUMN order_type TYPE ordertype
            USING CASE order_type::text
                WHEN 'MARKETPLACE' THEN 'marketplace'::ordertype
                WHEN 'PROCUREMENT' THEN 'procurement'::ordertype
                WHEN 'FULFILLMENT' THEN 'fulfillment'::ordertype
                ELSE 'marketplace'::ordertype
            END,
            ALTER COLUMN order_type SET DEFAULT 'marketplace'::ordertype
    """)
    op.execute("DROP TYPE ordertype_old")


def downgrade() -> None:
    op.execute("ALTER TYPE ordertype RENAME TO ordertype_new")
    op.execute("""
        CREATE TYPE ordertype AS ENUM (
            'MARKETPLACE',
            'PROCUREMENT',
            'FULFILLMENT'
        )
    """)
    op.execute("""
        ALTER TABLE orders
            ALTER COLUMN order_type DROP DEFAULT,
            ALTER COLUMN order_type TYPE ordertype
            USING CASE order_type::text
                WHEN 'marketplace' THEN 'MARKETPLACE'::ordertype
                WHEN 'procurement' THEN 'PROCUREMENT'::ordertype
                WHEN 'fulfillment' THEN 'FULFILLMENT'::ordertype
                ELSE 'MARKETPLACE'::ordertype
            END,
            ALTER COLUMN order_type SET DEFAULT 'MARKETPLACE'::ordertype
    """)
    op.execute("DROP TYPE ordertype_new")