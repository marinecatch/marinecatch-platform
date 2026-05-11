# app/models/order.py
#
# WHY THIS FILE EXISTS:
# Defines the orders table in PostgreSQL.
# Every purchase, from Neptune Hotels ordering tuna
# to Samaki Samaki ordering octopus, is stored here.
#
# Also supports Mode 2 (direct procurement) later:
# order_type = "marketplace" or "procurement" or "fulfillment"

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING    = "pending"
    CONFIRMED  = "confirmed"
    DISPATCHED = "dispatched"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"

class OrderType(str, enum.Enum):
    MARKETPLACE   = "marketplace"    # Mode 1 — fisher lists, buyer orders
    PROCUREMENT   = "procurement"    # Mode 2 — MarineCatch buys directly
    FULFILLMENT   = "fulfillment"    # Mode 3 — pre-order/contract supply

class Order(Base):
    __tablename__ = "orders"

    id                = Column(Integer, primary_key=True, index=True)
    listing_id        = Column(Integer, ForeignKey("fish_listings.id"), nullable=False)
    buyer_id          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fisherman_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_type        = Column(SAEnum(OrderType), default=OrderType.MARKETPLACE)
    species           = Column(String(50), nullable=False)
    landing_site      = Column(String(50), nullable=True)
    quantity_kg       = Column(Float, nullable=False)
    price_per_kg      = Column(Float, nullable=False)
    total_kes         = Column(Float, nullable=False)
    platform_fee_kes  = Column(Float, nullable=False)
    net_to_fisher_kes = Column(Float, nullable=False)
    commission_rate   = Column(String(10), nullable=False)
    delivery_address  = Column(String(300), nullable=False)
    notes             = Column(Text, nullable=True)
    status            = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING, index=True)
    updated_by        = Column(String(100), nullable=True)
    # ESG + logistics
    delivery_distance_km = Column(Float, nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    listing = relationship("FishListing", back_populates="orders")
    buyer   = relationship("User", back_populates="orders",
                           foreign_keys=[buyer_id])

    def __repr__(self):
        return f"<Order id={self.id} species={self.species} status={self.status}>"