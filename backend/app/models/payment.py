# app/models/payment.py
#
# WHY THIS FILE EXISTS:
# PaymentTransaction is the financial ledger of MarineCatch Africa.
# Every money movement — inbound from buyers, outbound to fishers —
# is recorded here with full breakdown.
#
# This is NOT a simple "payment success/fail" table.
# It is a finance ledger that supports:
# - M-Pesa STK Push (retail buyers)
# - Manual Paybill confirmation (institutional buyers)
# - Bank transfer logging
# - Credit sales (Net 1 / Net 7 / Net 14)
# - Fisher payouts (B2C M-Pesa)
# - Future: escrow, installments, multi-currency
#
# One order can have MULTIPLE payment transactions:
# - A processor pays 30% deposit today
# - Settles balance on delivery
# Both are separate PaymentTransaction records.
#
# Payment direction:
# INBOUND  = buyer pays MarineCatch
# OUTBOUND = MarineCatch pays fisher/supplier/agent

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class PaymentStatus(str, enum.Enum):
    PENDING          = "pending"           # Created, awaiting action
    PROCESSING       = "processing"        # STK Push sent, waiting response
    AUTHORIZED       = "authorized"        # Approved but not yet settled
    PARTIALLY_PAID   = "partially_paid"    # Deposit received, balance pending
    PAID             = "paid"              # Fully settled
    FAILED           = "failed"            # Payment attempt failed
    EXPIRED          = "expired"           # STK Push timed out
    REFUNDED         = "refunded"          # Money returned to buyer
    REVERSED         = "reversed"          # Bank/M-Pesa reversal
    ON_CREDIT        = "on_credit"         # Invoice issued, payment due later


class PaymentChannel(str, enum.Enum):
    MPESA            = "mpesa"
    BANK             = "bank"
    CASH             = "cash"
    CARD             = "card"
    CREDIT           = "credit"            # Institutional credit account
    CRYPTO           = "crypto"            # Future


class PaymentMethod(str, enum.Enum):
    MPESA_STK        = "mpesa_stk"         # STK Push to buyer phone
    MPESA_PAYBILL    = "mpesa_paybill"     # Manual Paybill payment
    MPESA_B2C        = "mpesa_b2c"         # Payout to fisher phone
    BANK_TRANSFER    = "bank_transfer"
    CASH             = "cash"
    CARD_ONLINE      = "card_online"
    CREDIT_TERMS     = "credit_terms"      # Invoice-based
    CRYPTO_FUTURE    = "crypto_future"


class PaymentDirection(str, enum.Enum):
    INBOUND          = "inbound"           # Buyer → MarineCatch
    OUTBOUND         = "outbound"          # MarineCatch → Fisher/Supplier


class PaymentPurpose(str, enum.Enum):
    ORDER_PAYMENT    = "order_payment"     # Standard buyer payment
    DEPOSIT          = "deposit"           # Partial upfront payment
    FINAL_SETTLEMENT = "final_settlement"  # Balance after deposit
    REFUND           = "refund"            # Money back to buyer
    FISHER_PAYOUT    = "fisher_payout"     # MarineCatch → Fisher
    ADVANCE_PAYMENT  = "advance_payment"   # Trip advance to fisher/agent
    LOGISTICS_PAYMENT = "logistics_payment" # Paying transporter
    STORAGE_PAYMENT  = "storage_payment"   # Paying cold storage
    CREDIT_SETTLEMENT = "credit_settlement" # Settling credit account


class CreditStatus(str, enum.Enum):
    NOT_APPLICABLE   = "not_applicable"
    PENDING_APPROVAL = "pending_approval"
    APPROVED         = "approved"
    OVERDUE          = "overdue"
    SETTLED          = "settled"
    DEFAULTED        = "defaulted"


class PayoutStatus(str, enum.Enum):
    NOT_APPLICABLE   = "not_applicable"    # Not a payout transaction
    PENDING          = "pending"           # Payout not yet initiated
    PROCESSING       = "processing"        # B2C sent, awaiting confirmation
    PAID             = "paid"              # Fisher received money
    FAILED           = "failed"            # Payout failed
    ON_HOLD          = "on_hold"           # Admin hold


# ── MODEL ─────────────────────────────────────────────────────────

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    # ── IDENTITY ──────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    transaction_reference = Column(String(50), unique=True, nullable=False, index=True)
    # Format: MC-PAY-YYYYMMDD-XXXXX
    # Example: MC-PAY-20260514-00001
    # Human readable, printable on receipts, searchable

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    # Nullable: some payments (advances, logistics) may not link to an order

    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Who is paying — buyer, or null for cash

    payee_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Who receives — fisher, supplier, agent, logistics partner

    payment_direction = Column(
        SAEnum(PaymentDirection, name="paymentdirection", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentDirection.INBOUND
    )
    # INBOUND = money coming in, OUTBOUND = money going out

    payment_purpose = Column(
        SAEnum(PaymentPurpose, name="paymentpurpose", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentPurpose.ORDER_PAYMENT
    )

    payment_channel = Column(
        SAEnum(PaymentChannel, name="paymentchannel", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentChannel.MPESA
    )

    payment_method = Column(
        SAEnum(PaymentMethod, name="paymentmethod", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentMethod.MPESA_STK
    )

    payment_provider = Column(String(50), nullable=True)
    # safaricom, equity, kcb, co-op, stripe_future

    # ── MONEY BREAKDOWN ───────────────────────────────────────
    # Store every component — critical for audits and payouts
    currency      = Column(String(10), default="KES", nullable=False)
    exchange_rate = Column(Float, default=1.0, nullable=True)
    # 1.0 for KES, actual rate for USD/EUR transactions

    subtotal_amount     = Column(Float, default=0.0, nullable=True)
    # Fish value only — before fees

    commission_amount   = Column(Float, default=0.0, nullable=True)
    # MarineCatch platform commission

    storage_fee_amount  = Column(Float, default=0.0, nullable=True)
    handling_fee_amount = Column(Float, default=0.0, nullable=True)
    qa_fee_amount       = Column(Float, default=0.0, nullable=True)
    logistics_fee_amount = Column(Float, default=0.0, nullable=True)
    tax_amount          = Column(Float, default=0.0, nullable=True)
    # VAT — future, once tax registration complete

    total_amount = Column(Float, nullable=False)
    # What buyer actually pays — sum of all components

    # ── PAYMENT STATUS ────────────────────────────────────────
    payment_status = Column(
        SAEnum(PaymentStatus, name="paymentstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True
    )

    # ── CREDIT TERMS ──────────────────────────────────────────
    is_credit_sale       = Column(Boolean, default=False, nullable=False)
    credit_due_date      = Column(DateTime(timezone=True), nullable=True)
    credit_status        = Column(
        SAEnum(CreditStatus, name="creditstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=CreditStatus.NOT_APPLICABLE,
        nullable=True
    )
    approved_by          = Column(String(100), nullable=True)
    # Admin who approved credit sale

    credit_limit_snapshot = Column(Float, nullable=True)
    # Buyer's credit limit at time of sale — for audit

    # ── M-PESA FIELDS ─────────────────────────────────────────
    mpesa_receipt_number  = Column(String(50), nullable=True, index=True)
    # Safaricom confirmation code — e.g. QJK3X2Y1Z0

    mpesa_phone_number    = Column(String(20), nullable=True)
    # Phone number that initiated payment

    checkout_request_id   = Column(String(100), nullable=True)
    # STK Push CheckoutRequestID from Safaricom

    merchant_request_id   = Column(String(100), nullable=True)
    # STK Push MerchantRequestID from Safaricom

    # ── BANK FIELDS ───────────────────────────────────────────
    bank_reference = Column(String(100), nullable=True)
    bank_name      = Column(String(100), nullable=True)
    account_name   = Column(String(100), nullable=True)

    # ── CARD FIELDS (FUTURE) ──────────────────────────────────
    card_last4        = Column(String(4), nullable=True)
    gateway_reference = Column(String(100), nullable=True)

    # ── FISHER PAYOUT TRACKING ────────────────────────────────
    # MarineCatch receives buyer payment first
    # Then pays fisher/supplier separately
    supplier_amount   = Column(Float, nullable=True)
    # What fisher/supplier receives after commission

    marinecatch_amount = Column(Float, nullable=True)
    # What MarineCatch keeps — commission + fees

    payout_status = Column(
        SAEnum(PayoutStatus, name="payoutstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=PayoutStatus.NOT_APPLICABLE,
        nullable=True
    )
    payout_date      = Column(DateTime(timezone=True), nullable=True)
    payout_reference = Column(String(100), nullable=True)
    # M-Pesa B2C transaction ID when fisher is paid

    # ── AUDIT + COMPLIANCE ────────────────────────────────────
    confirmed_by = Column(String(100), nullable=True)
    # Admin who manually confirmed payment

    paid_at      = Column(DateTime(timezone=True), nullable=True)
    # Exact timestamp payment was confirmed

    notes        = Column(Text, nullable=True)

    # ── FUTURE-READY ──────────────────────────────────────────
    country           = Column(String(10), default="KE", nullable=True)
    blockchain_tx_hash = Column(String(200), nullable=True)
    wallet_address    = Column(String(200), nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    order = relationship("Order", foreign_keys=[order_id])
    payer = relationship("User", foreign_keys=[payer_user_id])
    payee = relationship("User", foreign_keys=[payee_user_id])

    def __repr__(self):
        return (
            f"<PaymentTransaction {self.transaction_reference} "
            f"{self.payment_direction} "
            f"{self.total_amount} {self.currency} "
            f"status={self.payment_status}>"
        )