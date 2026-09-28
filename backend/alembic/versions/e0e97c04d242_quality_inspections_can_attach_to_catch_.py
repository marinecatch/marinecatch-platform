"""Quality inspections can attach to catch drafts

Revision ID: e0e97c04d242
Revises: 0dec84310338
Create Date: 2026-09-28 20:27:11.577894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0e97c04d242'
down_revision: Union[str, Sequence[str], None] = '0dec84310338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('quality_inspections', 'lot_id',
                    existing_type=sa.Integer(), nullable=True)
    op.add_column('quality_inspections',
                  sa.Column('draft_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_quality_inspections_draft_id',
                          'quality_inspections', 'catch_drafts',
                          ['draft_id'], ['id'])
    op.create_index('ix_quality_inspections_draft_id',
                    'quality_inspections', ['draft_id'], unique=True)
    op.alter_column('quality_inspections', 'grade',
                    existing_type=sa.String(length=2),
                    type_=sa.String(length=10))

def downgrade() -> None:
    op.drop_index('ix_quality_inspections_draft_id', table_name='quality_inspections')
    op.drop_constraint('fk_quality_inspections_draft_id',
                       'quality_inspections', type_='foreignkey')
    op.drop_column('quality_inspections', 'draft_id')
    op.alter_column('quality_inspections', 'grade',
                    existing_type=sa.String(length=10),
                    type_=sa.String(length=2))
    # lot_id stays nullable: making it NOT NULL again would fail
    # if draft-only inspections exist.
