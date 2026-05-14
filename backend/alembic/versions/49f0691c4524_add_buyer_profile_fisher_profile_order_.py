"""Add buyer profile, fisher profile, order commercial fields

Revision ID: 49f0691c4524
Revises: c0999361adc9
Create Date: 2026-05-14 10:54:46.653172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49f0691c4524'
down_revision: Union[str, Sequence[str], None] = 'c0999361adc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create buyertype enum first
    op.execute("CREATE TYPE buyertype AS ENUM ('institutional', 'retail')")

    # Add new values to userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'partner'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'coordinator'")

    # Add order commercial fields
    op.add_column('orders', sa.Column('order_source', sa.String(length=50), nullable=True))
    op.add_column('orders', sa.Column('lpo_reference', sa.String(length=100), nullable=True))
    op.add_column('orders', sa.Column('reserved_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('payment_terms_days', sa.Integer(), nullable=True))

    # Add user commercial + profile fields
    op.add_column('users', sa.Column('buyer_type', sa.Enum('institutional', 'retail', name='buyertype', create_type=False), nullable=True))
    op.add_column('users', sa.Column('payment_terms_days', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('credit_limit_kes', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('requires_prepayment', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('region', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('nationality', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('home_port', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('species_expertise', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('avg_trip_duration_days', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('is_cross_border_fisher', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'is_cross_border_fisher')
    op.drop_column('users', 'avg_trip_duration_days')
    op.drop_column('users', 'species_expertise')
    op.drop_column('users', 'home_port')
    op.drop_column('users', 'nationality')
    op.drop_column('users', 'region')
    op.drop_column('users', 'requires_prepayment')
    op.drop_column('users', 'credit_limit_kes')
    op.drop_column('users', 'payment_terms_days')
    op.drop_column('users', 'buyer_type')
    op.drop_column('orders', 'payment_terms_days')
    op.drop_column('orders', 'reserved_until')
    op.drop_column('orders', 'lpo_reference')
    op.drop_column('orders', 'order_source')
    op.execute("DROP TYPE buyertype")