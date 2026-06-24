# app/models/fisher_advance.py
#
# Fisher advance / inventory-backed financing.
# Fisher logs inventory → MarineCatch advances % of value immediately.
# Recovered when buyer pays.

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Boolean
from datetime import datetime, timezone
from app.database.connection import Base
import enum


class AdvanceStatus(str, enum.Enum):
    REQUESTED  = "requested"
    APPROVED   = "approved"
    DISBURSED  = "disbursed"
    RECOVERING = "recovering"   # Buyer paid, recovering advance
    RECOVERED  = "recovered"    # Fully recovered
    DEFAULTED  = "defaulted"


class FisherAdvance(Base):
    __tablename__ = "fisher_advances"

    id               = Column(Integer, primary_key=True, index=True)
    fisher_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    lot_id           = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)
    order_id         = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # Advance details
    lot_value_kes    = Column(Float, nullable=False)   # Total inventory value
    advance_rate     = Column(Float, default=0.70)     # 70% advance rate
    advance_amount_kes = Column(Float, nullable=False)  # lot_value * advance_rate
    advance_fee_kes  = Column(Float, default=0.0)      # MarineCatch fee for advance
    fee_rate         = Column(Float, default=0.03)     # 3% advance fee

    # Recovery
    recovered_kes    = Column(Float, default=0.0)
    outstanding_kes  = Column(Float, default=0.0)

    # Status
    status           = Column(Enum(AdvanceStatus), default=AdvanceStatus.REQUESTED)

    # M-Pesa disbursement
    mpesa_reference  = Column(String, nullable=True)
    disbursed_at     = Column(DateTime(timezone=True), nullable=True)
    recovered_at     = Column(DateTime(timezone=True), nullable=True)

    # Approval
    approved_by      = Column(String, nullable=True)
    approved_at      = Column(DateTime(timezone=True), nullable=True)
    notes            = Column(String, nullable=True)

    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at       = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))