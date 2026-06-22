"""Add visibility field to inventory_lots

Revision ID: 7989d7a3a22e
Revises: 06a4126b521d
Create Date: 2026-06-22 13:30:05.131920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7989d7a3a22e'
down_revision: Union[str, Sequence[str], None] = '06a4126b521d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventory_lots', sa.Column('visibility', sa.String(length=20), nullable=True))
    op.execute("UPDATE inventory_lots SET visibility = 'public' WHERE visibility IS NULL")
    op.alter_column('inventory_lots', 'visibility', nullable=False)
    op.create_index(op.f('ix_inventory_lots_visibility'), 'inventory_lots', ['visibility'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_lots_visibility'), table_name='inventory_lots')
    op.drop_column('inventory_lots', 'visibility')
