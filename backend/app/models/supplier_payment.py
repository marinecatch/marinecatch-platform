# app/models/supplier_payment.py
#
# WHY THIS FILE EXISTS:
# Tracks money owed BY MarineCatch to fishers and suppliers.
# Each delivery from a supplier creates a payable.
#
# MarineCatch buys from fishers/suppliers and pays them
# immediately, NET 3, NET 7, or NET 14 depending on arrangement.
# Shimoni supplier currently accepts deferred payment.
# Small fishers need immediate payment.

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum


class SupplierPaymentStatus(str, enum.Enum):
    PENDING      = "pending"       # Delivery received, payment not yet made
    SCHEDULED    = "scheduled"     # Payment date set
    PROCESSING   = "processing"    # M-Pesa or bank transfer initiated
    PAID         = "paid"          # Payment confirmed
    PARTIAL      = "partial"       # Partial payment made
    OVERDUE      = "overdue"       # Past agreed payment date


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id                  = Column(Integer, primary_key=True, index=True)

    # Reference
    reference           = Column(String(50), unique=True, nullable=False, index=True)
    lot_id              = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)
    order_id            = Column(Integer, ForeignKey("orders.id"), nullable=True)
    supplier_id         = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Amounts
    purchase_amount_kes = Column(Float, nullable=False)   # What MarineCatch agreed to pay
    paid_amount_kes     = Column(Float, default=0.0)      # What has been paid so far
    outstanding_kes     = Column(Float, nullable=False)   # Still owed

    # Payment terms agreed with this supplier
    payment_terms       = Column(String(20), default="immediate")
    # immediate, net_3, net_7, net_14, net_30

    # Dates
    delivery_date       = Column(DateTime(timezone=True), nullable=True)
    agreed_payment_date = Column(DateTime(timezone=True), nullable=True)
    paid_date           = Column(DateTime(timezone=True), nullable=True)

    # Status
    status              = Column(Enum(SupplierPaymentStatus), default=SupplierPaymentStatus.PENDING)

    # Payment details
    payment_method      = Column(String(30), nullable=True)
    # mpesa_b2c, bank_transfer, cash, pesa_link
    mpesa_reference     = Column(String(100), nullable=True)
    bank_reference      = Column(String(100), nullable=True)

    # Delivery details
    species             = Column(String(100), nullable=True)
    quantity_kg         = Column(Float, nullable=True)
    quality_grade       = Column(String(10), nullable=True)

    # Internal
    created_by          = Column(String(100), nullable=True)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    supplier            = relationship("User", foreign_keys=[supplier_id])