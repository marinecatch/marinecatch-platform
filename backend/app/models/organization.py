# app/models/organization.py
#
# WHY THIS FILE EXISTS:
# Enterprise buyers like Alpha Seafood, Kuza Freezer, and Sea Harvest
# need an organizational account that sits above individual users.
#
# One organization can have multiple users:
#   Alpha Seafood → procurement manager, logistics officer, finance
#
# Organization tier determines:
#   - Commission rates (marketplace vs enterprise)
#   - API access
#   - Inventory visibility permissions
#   - Subscription pricing
#
# OOC11 feedback: Alpha Seafood asked about:
#   - data ownership
#   - commercial confidentiality
#   - customer ownership
# Organization model is the foundation for answering all three.

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class OrgTier(str, enum.Enum):
    FREE        = "free"         # Basic marketplace access
    STANDARD    = "standard"     # Standard subscription
    ENTERPRISE  = "enterprise"   # Enterprise subscription
    API_PARTNER = "api_partner"  # API access tier
    SYSTEM      = "system"       # Internal MarineCatch use


class OrgType(str, enum.Enum):
    PROCESSOR    = "processor"    # Sea Harvest, Alpha Seafood
    EXPORTER     = "exporter"     # Export companies
    HOTEL        = "hotel"        # Neptune Hotels
    RESTAURANT   = "restaurant"   # Samaki Samaki
    WHOLESALER   = "wholesaler"   # Seafood Centre
    AGGREGATOR   = "aggregator"   # Kuza Freezer, Juma Riziki
    RETAILER     = "retailer"     # Supermarkets
    FISHER_COOP  = "fisher_coop"  # Fisher cooperatives
    SYSTEM       = "system"       # Internal


class OrgStatus(str, enum.Enum):
    ACTIVE      = "active"
    PENDING     = "pending"       # Applied, awaiting verification
    VERIFIED    = "verified"      # KYC completed
    SUSPENDED   = "suspended"
    INACTIVE    = "inactive"


# ── MODEL ─────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    # ── IDENTITY ──────────────────────────────────────────────
    id              = Column(Integer, primary_key=True, index=True)
    org_code        = Column(String(30), unique=True, nullable=False, index=True)
    # e.g. "ORG-ALPHA-001", "ORG-NEPTUNE-001"

    name            = Column(String(150), nullable=False, index=True)
    # e.g. "Alpha Seafood Kenya Ltd"

    trading_name    = Column(String(150), nullable=True)
    # e.g. "Alpha Seafood" — shorter display name

    # ── CLASSIFICATION ────────────────────────────────────────
    org_type        = Column(
        SAEnum(OrgType, name="orgtype", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrgType.WHOLESALER
    )

    org_tier        = Column(
        SAEnum(OrgTier, name="orgtier", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrgTier.FREE,
        index=True
    )

    org_status      = Column(
        SAEnum(OrgStatus, name="orgstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrgStatus.PENDING,
        index=True
    )

    # ── CONTACT ───────────────────────────────────────────────
    primary_contact_name  = Column(String(100), nullable=True)
    primary_contact_email = Column(String(255), nullable=True)
    primary_contact_phone = Column(String(20), nullable=True)

    billing_email   = Column(String(255), nullable=True)
    website         = Column(String(200), nullable=True)

    # ── LOCATION ──────────────────────────────────────────────
    address         = Column(String(300), nullable=True)
    city            = Column(String(100), nullable=True)
    county          = Column(String(100), nullable=True)
    country         = Column(String(50), default="Kenya", nullable=False)

    # ── REGISTRATION ──────────────────────────────────────────
    registration_number = Column(String(100), nullable=True)
    # Kenya company registration number

    kra_pin         = Column(String(50), nullable=True)
    # KRA PIN for tax compliance

    kebs_number     = Column(String(50), nullable=True)
    # KEBS registration for food businesses

    # ── SUBSCRIPTION ──────────────────────────────────────────
    subscription_plan   = Column(String(30), default="basic", nullable=False)
    # basic, standard, enterprise, api

    subscription_start  = Column(DateTime(timezone=True), nullable=True)
    subscription_expiry = Column(DateTime(timezone=True), nullable=True)
    monthly_fee_kes     = Column(Float, default=0.0, nullable=True)

    # ── API ACCESS ────────────────────────────────────────────
    api_access_enabled  = Column(Boolean, default=False, nullable=False)
    api_key_hash        = Column(String(200), nullable=True)
    # Hashed API key — never store plaintext

    api_rate_limit_per_hour = Column(Integer, default=100, nullable=True)
    # Requests per hour limit

    # ── DATA GOVERNANCE ───────────────────────────────────────
    # OOC11: Alpha Seafood asked about data ownership
    data_sharing_consent    = Column(Boolean, default=False, nullable=False)
    # Has org consented to anonymized data use?

    can_see_market_prices   = Column(Boolean, default=True, nullable=False)
    # Can see aggregated market price intelligence?

    inventory_visibility    = Column(String(20), default="public", nullable=False)
    # Default visibility for this org's inventory lots
    # public, partner_only, private

    # ── VOLUME TRACKING ───────────────────────────────────────
    total_orders        = Column(Integer, default=0, nullable=True)
    total_spend_kes     = Column(Float, default=0.0, nullable=True)
    total_kg_purchased  = Column(Float, default=0.0, nullable=True)
    # Updated by order service on each transaction

    # ── ACCOUNT OWNER ─────────────────────────────────────────
    owner_user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    # The primary admin user for this organization

    # ── METADATA ──────────────────────────────────────────────
    is_active       = Column(Boolean, default=True, nullable=False)
    is_verified     = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    notes           = Column(Text, nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    owner           = relationship("User", foreign_keys=[owner_user_id])

    def __repr__(self):
        return (
            f"<Organization {self.org_code} "
            f"{self.name} "
            f"tier={self.org_tier} "
            f"status={self.org_status}>"
        )