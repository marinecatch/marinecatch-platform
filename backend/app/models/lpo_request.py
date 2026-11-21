# app/models/lpo_request.py
#
# WHY THIS FILE EXISTS:
# Buyer-facing front door to the existing LPO flow.
# Institutional buyers (hotels, wholesalers) submit a purchase
# order request here — species + quantities + their own LPO
# reference and payment terms — WITHOUT picking a specific
# inventory lot, since buyers don't see lot-level stock detail.
#
# Admin reviews each request and, item by item, assigns a real
# lot_id and calls the existing create_lpo_order() in
# lpo_service.py — that function is untouched by this feature.
# This table only represents the request BEFORE it becomes
# real Order records.

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class LPORequest(Base):
    __tablename__ = "lpo_requests"

    id = Column(Integer, primary_key=True, index=True)

    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    lpo_reference        = Column(String(100), nullable=False)
    # The buyer's own PO number, e.g. "LPO-2026-0142"

    procurement_officer  = Column(String(100), nullable=True)
    expected_fulfillment_date = Column(String(20), nullable=True)
    payment_terms_days   = Column(Integer, default=7, nullable=False)
    delivery_address     = Column(Text, nullable=True)
    notes                = Column(Text, nullable=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    # pending, approved, rejected

    reviewed_by       = Column(String(100), nullable=True)
    reviewed_at       = Column(DateTime(timezone=True), nullable=True)
    rejection_reason  = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    buyer = relationship("User", foreign_keys=[buyer_id])
    items = relationship("LPORequestItem", back_populates="lpo_request", cascade="all, delete-orphan")


class LPORequestItem(Base):
    __tablename__ = "lpo_request_items"

    id = Column(Integer, primary_key=True, index=True)
    lpo_request_id = Column(Integer, ForeignKey("lpo_requests.id"), nullable=False, index=True)

    species      = Column(String(50), nullable=False)
    quantity_kg  = Column(Float, nullable=False)
    notes        = Column(Text, nullable=True)

    # Filled in by admin at approval time — which lot actually
    # fulfilled this line, and which resulting Order it became.
    fulfilled_lot_id   = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)
    resulting_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    lpo_request = relationship("LPORequest", back_populates="items")