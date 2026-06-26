"""Add trade_receivables and supplier_payments tables
Revision ID: 44c6252bac63
Revises: c760f4cebfe9
Create Date: 2026-06-24 13:56:14.143437
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '44c6252bac63'
down_revision: Union[str, Sequence[str], None] = 'c760f4cebfe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('trade_receivables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('gross_amount_kes', sa.Float(), nullable=False),
        sa.Column('vat_kes', sa.Float(), nullable=True),
        sa.Column('total_amount_kes', sa.Float(), nullable=False),
        sa.Column('paid_amount_kes', sa.Float(), nullable=True),
        sa.Column('outstanding_kes', sa.Float(), nullable=False),
        sa.Column('payment_terms', sa.String(20), nullable=True),
        sa.Column('delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('delivery_confirmed', sa.Boolean(), nullable=True),
        sa.Column('delivery_confirmed_by', sa.String(100), nullable=True),
        sa.Column('invoice_stamped', sa.Boolean(), nullable=True),
        sa.Column('etims_issued', sa.Boolean(), nullable=True),
        sa.Column('payment_method', sa.String(30), nullable=True),
        sa.Column('payment_reference', sa.String(100), nullable=True),
        sa.Column('payment_notes', sa.Text(), nullable=True),
        sa.Column('species', sa.String(100), nullable=True),
        sa.Column('quantity_kg', sa.Float(), nullable=True),
        sa.Column('delivery_location', sa.String(200), nullable=True),
        sa.Column('received_by', sa.String(100), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
    )
    op.create_index('ix_trade_receivables_id', 'trade_receivables', ['id'])
    op.create_index('ix_trade_receivables_invoice_number', 'trade_receivables', ['invoice_number'])

    op.create_table('supplier_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(50), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('purchase_amount_kes', sa.Float(), nullable=False),
        sa.Column('paid_amount_kes', sa.Float(), nullable=True),
        sa.Column('outstanding_kes', sa.Float(), nullable=False),
        sa.Column('payment_terms', sa.String(20), nullable=True),
        sa.Column('delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('agreed_payment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('payment_method', sa.String(30), nullable=True),
        sa.Column('mpesa_reference', sa.String(100), nullable=True),
        sa.Column('bank_reference', sa.String(100), nullable=True),
        sa.Column('species', sa.String(100), nullable=True),
        sa.Column('quantity_kg', sa.Float(), nullable=True),
        sa.Column('quality_grade', sa.String(10), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference'),
    )
    op.create_index('ix_supplier_payments_id', 'supplier_payments', ['id'])
    op.create_index('ix_supplier_payments_reference', 'supplier_payments', ['reference'])

    op.create_table('escrow_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=True),
        sa.Column('gross_amount_kes', sa.Float(), nullable=False),
        sa.Column('commission_kes', sa.Float(), nullable=True),
        sa.Column('net_to_seller_kes', sa.Float(), nullable=True),
        sa.Column('advance_paid_kes', sa.Float(), nullable=True),
        sa.Column('balance_to_release', sa.Float(), nullable=True),
        sa.Column('settlement_mode', sa.String(20), nullable=True),
        sa.Column('payment_terms', sa.String(20), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('held_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
    )
    op.create_index('ix_escrow_accounts_id', 'escrow_accounts', ['id'])

    op.create_table('fisher_advances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fisher_id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('lot_value_kes', sa.Float(), nullable=False),
        sa.Column('advance_rate', sa.Float(), nullable=True),
        sa.Column('advance_amount_kes', sa.Float(), nullable=False),
        sa.Column('advance_fee_kes', sa.Float(), nullable=True),
        sa.Column('fee_rate', sa.Float(), nullable=True),
        sa.Column('recovered_kes', sa.Float(), nullable=True),
        sa.Column('outstanding_kes', sa.Float(), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('mpesa_reference', sa.String(100), nullable=True),
        sa.Column('disbursed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['fisher_id'], ['users.id']),
        sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fisher_advances_id', 'fisher_advances', ['id'])


def downgrade() -> None:
    op.drop_table('fisher_advances')
    op.drop_table('escrow_accounts')
    op.drop_table('supplier_payments')
    op.drop_table('trade_receivables')