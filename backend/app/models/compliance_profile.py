# app/models/compliance_profile.py
#
# WHY THIS FILE EXISTS:
# Every participant on MarineCatch Africa has a compliance profile.
# This separates identity verification, tax compliance, and trust
# from the core User model — keeping User clean while giving us
# a flexible framework for future integrations with KRA, KFS,
# export certification bodies, and financial institutions.
#
# Compliance levels:
# 0 = Lead (enquired, not yet registered)
# 1 = Registered (phone + national ID)
# 2 = Verified (BMU/business confirmed)
# 3 = Tax Compliant (KRA PIN verified)
# 4 = Export Ready (health cert, traceability, sustainability)
#
# Buyer tiers:
# 0 = Guest (browse only)
# 1 = Individual (M-Pesa, prepaid)
# 2 = Business (hotels, restaurants, processors)
# 3 = Institutional (supermarkets, hospitals, government)
# 4 = Strategic (exporters, large processors, long-term contracts)

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, ForeignKey, Text)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class ComplianceProfile(Base):
    __tablename__ = "compliance_profiles"

    id                           = Column(Integer, primary_key=True, index=True)
    user_id                      = Column(Integer, ForeignKey("users.id"),
                                         unique=True, nullable=False, index=True)

    # ── MEMBER IDENTITY ───────────────────────────────────────────
    member_id                    = Column(String(20), unique=True, nullable=True, index=True)
    # Format: MC-FSH-000001, MC-BUY-000001, MC-SUP-000001,
    #         MC-LOG-000001, MC-EXP-000001

    # ── COMPLIANCE LEVEL ──────────────────────────────────────────
    compliance_level             = Column(Integer, default=0)
    # 0=Lead, 1=Registered, 2=Verified, 3=Tax Compliant, 4=Export Ready

    # ── IDENTITY VERIFICATION ─────────────────────────────────────
    national_id                  = Column(String(20), nullable=True)
    national_id_verified         = Column(Boolean, default=False)
    national_id_verified_at      = Column(DateTime(timezone=True), nullable=True)
    phone_verified               = Column(Boolean, default=False)
    phone_verified_at            = Column(DateTime(timezone=True), nullable=True)
    selfie_verified              = Column(Boolean, default=False)

    # ── FISHER / SUPPLIER SPECIFIC ────────────────────────────────
    bmu_membership_number        = Column(String(50), nullable=True)
    bmu_name                     = Column(String(100), nullable=True)
    bmu_verified                 = Column(Boolean, default=False)
    bmu_verified_at              = Column(DateTime(timezone=True), nullable=True)
    fisher_cluster_id            = Column(Integer,
                                         ForeignKey("fisher_clusters.id"),
                                         nullable=True)
    vessel_registration          = Column(String(50), nullable=True)
    gear_type                    = Column(String(50), nullable=True)
    default_landing_site         = Column(String(100), nullable=True)

    # ── BUSINESS / TAX ────────────────────────────────────────────
    kra_pin                      = Column(String(20), nullable=True)
    kra_verified                 = Column(Boolean, default=False)
    kra_verified_at              = Column(DateTime(timezone=True), nullable=True)
    business_registration_number = Column(String(50), nullable=True)
    business_type                = Column(String(50), nullable=True)
    # sole_trader, partnership, limited_company, cooperative, bmu
    tax_status                   = Column(String(30), default="unknown")
    # unknown, compliant, non_compliant, exempt
    etims_enabled                = Column(Boolean, default=False)
    etims_enabled_at             = Column(DateTime(timezone=True), nullable=True)

    # ── BUYER TIER ────────────────────────────────────────────────
    buyer_tier                   = Column(Integer, default=0)
    # 0=Guest, 1=Individual, 2=Business, 3=Institutional, 4=Strategic
    signed_agreement             = Column(Boolean, default=False)
    signed_agreement_at          = Column(DateTime(timezone=True), nullable=True)

    # ── EXPORT READINESS ──────────────────────────────────────────
    health_certificate           = Column(Boolean, default=False)
    sustainability_certified     = Column(Boolean, default=False)
    export_permit                = Column(Boolean, default=False)
    export_markets               = Column(String(200), nullable=True)
    # e.g. "EU, UAE, China"

    # ── TRUST SCORES (auto-calculated) ───────────────────────────
    trust_score                  = Column(Float, default=0.0)
    # 0-100, composite score
    quality_score                = Column(Float, default=0.0)
    # based on inspection pass rate
    delivery_reliability         = Column(Float, default=0.0)
    # % of deliveries on time
    payment_score                = Column(Float, default=0.0)
    # for buyers: on-time payment rate

    # ── OPERATIONAL HISTORY (auto-updated) ───────────────────────
    total_transactions           = Column(Integer, default=0)
    total_volume_kg              = Column(Float, default=0.0)
    total_value_kes              = Column(Float, default=0.0)
    rejection_rate               = Column(Float, default=0.0)
    on_time_delivery_rate        = Column(Float, default=0.0)
    months_active                = Column(Integer, default=0)

    # ── FIRST STAFF VERIFICATION ─────────────────────────────────
    verified_by                  = Column(String(100), nullable=True)
    # MarineCatch staff member who did first verification
    first_verified_at            = Column(DateTime(timezone=True), nullable=True)
    verification_notes           = Column(Text, nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────────
    created_at                   = Column(DateTime(timezone=True),
                                         default=lambda: datetime.now(timezone.utc))
    updated_at                   = Column(DateTime(timezone=True),
                                         onupdate=lambda: datetime.now(timezone.utc))

    # ── RELATIONSHIPS ─────────────────────────────────────────────
    user                         = relationship("User", foreign_keys=[user_id])
    cluster                      = relationship("FisherCluster",
                                               foreign_keys=[fisher_cluster_id])