# app/models/trade_receivable.py
#
# WHY THIS FILE EXISTS:
# Tracks money owed TO MarineCatch by buyers (hotels, processors, exporters).
# Each delivery to a buyer creates a receivable — a formal record of what they owe.
#
# This is the foundation of MarineCatch's working capital management.
# It powers: invoice tracking, overdue alerts, credit scoring, and
# the supplier payment queue.

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum


class ReceivableStatus(str, enum.Enum):
    INVOICED         = "invoiced"        # Invoice issued, awaiting payment
    PARTIALLY_PAID   = "partially_paid"  # Partial payment received
    PAID             = "paid"            # Fully paid
    OVERDUE          = "overdue"         # Past due date, unpaid
    DISPUTED         = "disputed"        # Payment in dispute
    WRITTEN_OFF      = "written_off"     # Bad debt


class PaymentMethod(str, enum.Enum):
    MPESA_PAYBILL    = "mpesa_paybill"
    BANK_TRANSFER    = "bank_transfer"
    PESA_LINK        = "pesa_link"
    CASH             = "cash"
    CHEQUE           = "cheque"


class TradeReceivable(Base):
    __tablename__ = "trade_receivables"

    id                  = Column(Integer, primary_key=True, index=True)

    # Reference
    invoice_number      = Column(String(50), unique=True, nullable=False, index=True)
    order_id            = Column(Integer, ForeignKey("orders.id"), nullable=True)
    buyer_id            = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Amounts
    gross_amount_kes    = Column(Float, nullable=False)   # Total invoice value
    vat_kes             = Column(Float, default=0.0)      # VAT if applicable
    total_amount_kes    = Column(Float, nullable=False)   # gross + VAT
    paid_amount_kes     = Column(Float, default=0.0)      # Amount received so far
    outstanding_kes     = Column(Float, nullable=False)   # total - paid

    # Payment terms
    payment_terms       = Column(String(20), default="net_30")
    # net_3, net_7, net_14, net_30, net_45, immediate

    # Dates
    delivery_date       = Column(DateTime(timezone=True), nullable=True)
    invoice_date        = Column(DateTime(timezone=True), nullable=True)
    due_date            = Column(DateTime(timezone=True), nullable=True)
    paid_date           = Column(DateTime(timezone=True), nullable=True)

    # Status
    status              = Column(Enum(ReceivableStatus), default=ReceivableStatus.INVOICED)

    # Delivery verification
    delivery_confirmed  = Column(Boolean, default=False)
    delivery_confirmed_by = Column(String(100), nullable=True)
    invoice_stamped     = Column(Boolean, default=False)  # Hotel procurement stamp
    etims_issued        = Column(Boolean, default=False)  # KRA eTIMS invoice

    # Payment record
    payment_method      = Column(Enum(PaymentMethod), nullable=True)
    payment_reference   = Column(String(100), nullable=True)  # Bank ref, M-Pesa ref
    payment_notes       = Column(Text, nullable=True)

    # Delivery details
    species             = Column(String(100), nullable=True)
    quantity_kg         = Column(Float, nullable=True)
    delivery_location   = Column(String(200), nullable=True)
    received_by         = Column(String(100), nullable=True)  # Hotel staff name

    # Internal
    created_by          = Column(String(100), nullable=True)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    buyer               = relationship("User", foreign_keys=[buyer_id])