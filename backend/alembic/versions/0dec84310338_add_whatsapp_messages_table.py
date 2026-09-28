"""Add whatsapp_messages table

Revision ID: 0dec84310338
Revises: b7f38a5d21c4
Create Date: 2026-08-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0dec84310338'
down_revision: Union[str, Sequence[str], None] = 'b7f38a5d21c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('whatsapp_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('button_id', sa.String(length=50), nullable=True),
        sa.Column('sender_name', sa.String(length=100), nullable=True),
        sa.Column('user_role', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_whatsapp_messages_id', 'whatsapp_messages', ['id'])
    op.create_index('ix_whatsapp_messages_phone_number', 'whatsapp_messages', ['phone_number'])
    op.create_index('ix_whatsapp_messages_created_at', 'whatsapp_messages', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_whatsapp_messages_created_at', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_phone_number', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_id', table_name='whatsapp_messages')
    op.drop_table('whatsapp_messages')