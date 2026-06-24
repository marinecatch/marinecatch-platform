# app/models/user.py
#
# WHY THIS FILE EXISTS:
# Defines the users table in PostgreSQL.
# Every fisher, buyer, supplier, partner, coordinator,
# and admin is stored here.
#
# Real examples:
# Abdalla Masudi  — fisher     — Kibuyuni
# Neptune Hotels  — buyer      — Diani
# Juma Riziki     — supplier   — Kinondo
# Eldoret Partner — partner    — Eldoret
# BMU Coordinator — coordinator— Shimoni

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class UserRole(str, enum.Enum):
    FISHER      = "fisher"       # Individual fishers at landing sites
    SUPPLIER    = "supplier"     # Fish traders and aggregators
    BUYER       = "buyer"        # Hotels, restaurants, wholesalers
    ADMIN       = "admin"        # MarineCatch staff
    PARTNER     = "partner"      # Regional distribution partners (e.g. Eldoret)
    COORDINATOR = "coordinator"  # Procurement coordinators / former agents


class BuyerType(str, enum.Enum):
    INSTITUTIONAL = "institutional"  # Hotels, processors, exporters — invoice terms
    RETAIL        = "retail"         # Individual, WhatsApp, B2C — prepayment required


class User(Base):
    __tablename__ = "users"

    # ── IDENTITY ─────────────────────────────────────────────
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    phone           = Column(String(20), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(
        SAEnum(UserRole, name="userrole", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=UserRole.FISHER,
        nullable=False
    )
    location        = Column(String(200), nullable=True)
    business_name   = Column(String(200), nullable=True)

    # ── BUYER COMMERCIAL PROFILE ──────────────────────────────
    # Drives payment logic — institutional vs retail behave differently
    buyer_type      = Column(
        SAEnum(BuyerType, name="buyertype", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    # 0 = prepay, 1 = same day, 3 = Net 3, 7 = Net 7, 14 = Net 14
    payment_terms_days  = Column(Integer, default=0, nullable=True)
    # Maximum credit allowed — null = no credit
    credit_limit_kes    = Column(Float, nullable=True)
    # If True: payment must be received before fulfillment
    requires_prepayment = Column(Boolean, default=True, nullable=True)

    # ── REGIONAL + NETWORK PROFILE ────────────────────────────
    # Coast, Nairobi, Rift Valley, Western, Eastern, Remote
    region              = Column(String(100), nullable=True)

    # ── FISHER / CROSS-BORDER PROFILE ─────────────────────────
    # Captures Tanzanian, Pemba, Mozambican fishers operating in Kenya
    nationality             = Column(String(50), nullable=True)
    home_port               = Column(String(100), nullable=True)
    # e.g. "tuna,octopus,lobster" — future: JSON
    species_expertise       = Column(String(200), nullable=True)
    avg_trip_duration_days  = Column(Integer, nullable=True)
    # True for Tanzanian/Pemba fishers working with Kenyan permits
    is_cross_border_fisher  = Column(Boolean, default=False, nullable=True)

    # ── ESG + COMPLIANCE ──────────────────────────────────────
    gender              = Column(String(10), nullable=True)
    bmu_membership_id   = Column(String(50), nullable=True)
    fishing_license_no  = Column(String(50), nullable=True)
    license_expiry_date = Column(String(20), nullable=True)

# ── SETTLEMENT ACCOUNT ────────────────────────────────────────
    # Where MarineCatch sends payouts — fisher M-Pesa, bank, cooperative
    # settlement_account_type: MPESA, BANK, COOPERATIVE, WALLET, CASH, CRYPTO
    settlement_account_id       = Column(String(100), nullable=True)
    settlement_account_type     = Column(String(30),  nullable=True)
    settlement_account_verified = Column(Boolean, default=False, nullable=False)
    # Organization linkage
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    buyer_type      = Column(String(30), nullable=True)
    # individual, hotel, restaurant, processor, exporter, wholesaler
    # Replaces multiple user roles with cleaner buyer_type field
    # ── STATUS + TIMESTAMPS ───────────────────────────────────
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    listings = relationship("FishListing", back_populates="fisher")
    orders   = relationship("Order", back_populates="buyer",
                            foreign_keys="Order.buyer_id")

    def __repr__(self):
        return f"<User id={self.id} name={self.name} role={self.role}>"

    # Credit and financial profile
    credit_score            = Column(String, default="unrated")
    credit_limit_kes        = Column(Float, default=0.0)
    payment_terms           = Column(String, default="immediate")
    outstanding_balance_kes = Column(Float, default=0.0)
    on_time_payment_rate    = Column(Float, default=0.0)
    total_orders_count      = Column(Integer, default=0)