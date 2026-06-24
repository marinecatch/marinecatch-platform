# app/models/escrow.py
#
# Escrow account for holding buyer payments until delivery confirmed.
# Separates payment collection from settlement and payout.

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum


class EscrowStatus(str, enum.Enum):
    HELD              = "held"
    PARTIALLY_RELEASED = "partially_released"
    RELEASED          = "released"
    REFUNDED          = "refunded"
    DISPUTED          = "disputed"


class SettlementMode(str, enum.Enum):
    INSTANT = "instant"    # MarineCatch-owned inventory, repeat buyers
    ESCROW  = "escrow"     # New buyers, large orders, hotels
    CREDIT  = "credit"     # Approved buyers on NET terms


class PaymentTerms(str, enum.Enum):
    IMMEDIATE = "immediate"
    NET_3     = "net_3"
    NET_7     = "net_7"
    NET_14    = "net_14"
    NET_30    = "net_30"
    NET_45    = "net_45"


class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"

    id               = Column(Integer, primary_key=True, index=True)
    order_id         = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    buyer_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id        = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Amounts
    gross_amount_kes      = Column(Float, nullable=False)
    commission_kes        = Column(Float, default=0.0)
    net_to_seller_kes     = Column(Float, default=0.0)
    advance_paid_kes      = Column(Float, default=0.0)
    balance_to_release    = Column(Float, default=0.0)

    # Settlement
    settlement_mode  = Column(Enum(SettlementMode), default=SettlementMode.ESCROW)
    payment_terms    = Column(Enum(PaymentTerms),   default=PaymentTerms.IMMEDIATE)
    status           = Column(Enum(EscrowStatus),   default=EscrowStatus.HELD)

    # Verification
    verified_by      = Column(String, nullable=True)
    verification_method = Column(String, nullable=True)
    # methods: buyer_confirmation, otp, delivery_photo, staff_verification, logistics

    # Timing
    held_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    due_date         = Column(DateTime(timezone=True), nullable=True)
    released_at      = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at       = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Notes
    notes            = Column(String, nullable=True)