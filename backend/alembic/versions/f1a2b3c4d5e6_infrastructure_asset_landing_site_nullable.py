"""Make InfrastructureAsset.landing_site_id nullable

Revision ID: f1a2b3c4d5e6
Revises: d4e8f0a3b6c9
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'f1a2b3c4d5e6'
down_revision = 'd4e8f0a3b6c9'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('infrastructure_assets', 'landing_site_id', nullable=True)


def downgrade():
    op.alter_column('infrastructure_assets', 'landing_site_id', nullable=False)