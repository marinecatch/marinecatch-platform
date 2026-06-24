# # app/models/order.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT  = "pending_payment"
    PAID             = "paid"
    CONFIRMED        = "confirmed"
    PREPARING        = "preparing"
    DISPATCHED       = "dispatched"
    DELIVERED        = "delivered"
    COMPLETED        = "completed"
    CANCELLED        = "cancelled"
    PAYMENT_FAILED   = "payment_failed"
    REFUNDED         = "refunded"


class OrderType(str, enum.Enum):
    MARKETPLACE   = "marketplace"
    PROCUREMENT   = "procurement"
    FULFILLMENT   = "fulfillment"


class Order(Base):
    __tablename__ = "orders"

    id                = Column(Integer, primary_key=True, index=True)
    listing_id        = Column(Integer, ForeignKey("fish_listings.id"), nullable=True)
    lot_id            = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True, index=True)
    buyer_id          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fisherman_id      = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    order_type        = Column(
        SAEnum(OrderType, name="ordertype", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=OrderType.MARKETPLACE
    )
    species           = Column(String(50), nullable=False)
    landing_site      = Column(String(50), nullable=True)
    quantity_kg       = Column(Float, nullable=False)
    price_per_kg      = Column(Float, nullable=False)
    total_kes         = Column(Float, nullable=False)
    platform_fee_kes  = Column(Float, nullable=False)
    net_to_fisher_kes = Column(Float, nullable=False)
    commission_rate   = Column(String(10), nullable=False)
    delivery_address  = Column(String(300), nullable=True)
    notes             = Column(Text, nullable=True)
    status            = Column(
        SAEnum(OrderStatus, name="orderstatus", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.PENDING_PAYMENT,
        index=True
    )
    updated_by        = Column(String(100), nullable=True)
    delivery_distance_km = Column(Float, nullable=True)
    # ── ORDER ORIGIN + COMMERCIAL TERMS ──────────────────────
    # How this order entered the system
    order_source        = Column(String(50), nullable=True)
    # e.g. "marketplace", "lpo", "whatsapp", "phone", "ussd"

    # LPO number from institutional buyer — links to their paperwork
    lpo_reference       = Column(String(100), nullable=True)

    # When reservation expires — null = no expiry (institutional buyers)
    # Set to 30 minutes from placement for retail/STK Push orders
    reserved_until      = Column(DateTime(timezone=True), nullable=True)

    # Payment terms copied from buyer at time of order
    # 0 = prepay, 1 = same day, 3 = Net 3, 7 = Net 7
    payment_terms_days  = Column(Integer, default=0, nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    listing  = relationship("FishListing", back_populates="orders")
    lot      = relationship("InventoryLot", foreign_keys=[lot_id])
    buyer    = relationship("User", back_populates="orders", foreign_keys=[buyer_id])

    def __repr__(self):
        return f"<Order id={self.id} species={self.species} status={self.status}>"

    # Payment and settlement
    payment_terms   = Column(String, default="immediate")
    settlement_mode = Column(String, default="escrow")
    due_date        = Column(DateTime(timezone=True), nullable=True)
    paid_at         = Column(DateTime(timezone=True), nullable=True)