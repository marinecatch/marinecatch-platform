# app/models/fisher_cluster.py
#
# WHY THIS FILE EXISTS:
# FisherCluster groups verified fishers at a landing site.
# Recommended by Alpha Seafood and Kuza Freezer at OOC11.
#
# Instead of onboarding hundreds of individual fishers,
# MarineCatch works with clusters of 5-20 verified fishers
# per landing site. This creates:
#   - Predictable supply volumes
#   - Easier compliance and verification
#   - Group savings and credit scoring
#   - Better procurement planning
#   - Pathway to group financing and insurance
#
# Real examples:
#   Kibuyuni Tuna Cluster — Abdalla, Bakari + 8 others
#   Shimoni Deep Sea Cluster — Said Mohamed + suppliers
#   Mwambao Octopus Cluster — Shee Sahare + coastal fishers

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class ClusterStatus(str, enum.Enum):
    ACTIVE      = "active"       # Fully operational
    PENDING     = "pending"      # Applied, not yet verified
    VERIFIED    = "verified"     # MarineCatch verified
    SUSPENDED   = "suspended"    # Temporarily inactive
    INACTIVE    = "inactive"     # No longer operating


class ClusterType(str, enum.Enum):
    ARTISANAL   = "artisanal"    # Small-scale fishers, traditional gear
    COMMERCIAL  = "commercial"   # Larger vessels, commercial gear
    AQUACULTURE = "aquaculture"  # Fish farmers, freshwater
    AGGREGATOR  = "aggregator"   # Supplier/trader cluster
    MIXED       = "mixed"        # Mixed fisher types


# ── MODEL ─────────────────────────────────────────────────────────

class FisherCluster(Base):
    __tablename__ = "fisher_clusters"

    # ── IDENTITY ──────────────────────────────────────────────
    id              = Column(Integer, primary_key=True, index=True)
    cluster_code    = Column(String(30), unique=True, nullable=False, index=True)
    # e.g. "KBY-TNA-001" (Kibuyuni Tuna Cluster 001)

    name            = Column(String(150), nullable=False, index=True)
    # e.g. "Kibuyuni Tuna Cluster"

    description     = Column(Text, nullable=True)

    # ── CLASSIFICATION ────────────────────────────────────────
    cluster_type    = Column(
        SAEnum(ClusterType, name="clustertype", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=ClusterType.ARTISANAL,
        nullable=False
    )

    cluster_status  = Column(
        SAEnum(ClusterStatus, name="clusterstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=ClusterStatus.PENDING,
        nullable=False,
        index=True
    )

    # ── LOCATION ──────────────────────────────────────────────
    landing_site    = Column(String(50), nullable=False, index=True)
    # kibuyuni, shimoni, vanga, ukunda, mwambao...

    county          = Column(String(50), nullable=True)
    # Kwale, Mombasa, Kilifi...

    country         = Column(String(30), default="Kenya", nullable=False)

    gps_lat         = Column(Float, nullable=True)
    gps_lng         = Column(Float, nullable=True)

    # ── BMU LINKAGE ───────────────────────────────────────────
    bmu_name        = Column(String(100), nullable=True)
    # Beach Management Unit name
    # e.g. "Kibuyuni BMU"

    bmu_registration_number = Column(String(50), nullable=True)
    # Official BMU registration with fisheries dept

    # ── SPECIES ───────────────────────────────────────────────
    species_specialization = Column(String(200), nullable=True)
    # Comma-separated: "tuna,kingfish,octopus"
    # What this cluster primarily catches

    gear_types      = Column(String(200), nullable=True)
    # "handline,longline,trap"
    # Important for sustainability and IUU compliance

    # ── MEMBERSHIP ────────────────────────────────────────────
    members_count   = Column(Integer, default=0, nullable=False)
    # Current active members

    min_members     = Column(Integer, default=5, nullable=True)
    max_members     = Column(Integer, default=20, nullable=True)
    # Recommended cluster size: 5-20 fishers

    # ── CAPACITY ──────────────────────────────────────────────
    weekly_capacity_kg  = Column(Float, nullable=True)
    # Estimated weekly supply volume

    monthly_capacity_kg = Column(Float, nullable=True)
    # Estimated monthly supply volume

    avg_catch_per_trip_kg = Column(Float, nullable=True)
    # Average catch per fishing trip per member

    active_vessels  = Column(Integer, nullable=True)
    # Number of boats in the cluster

    # ── FINANCIAL ─────────────────────────────────────────────
    savings_balance_kes = Column(Float, default=0.0, nullable=True)
    # Group savings pool — future: linked to group account

    credit_score    = Column(Float, default=0.0, nullable=True)
    # 0-100 — calculated from:
    # payment history, supply consistency, compliance rate
    # Used for: credit access, advance payments, insurance

    total_earnings_kes  = Column(Float, default=0.0, nullable=True)
    # Cumulative earnings through MarineCatch platform

    # ── COMPLIANCE ────────────────────────────────────────────
    is_verified     = Column(Boolean, default=False, nullable=False)
    # MarineCatch field verification done

    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)

    kebs_compliant  = Column(Boolean, default=False, nullable=True)
    # Kenya Bureau of Standards compliance

    has_iuu_training = Column(Boolean, default=False, nullable=True)
    # IUU (Illegal, Unreported, Unregulated) awareness training

    # ── CONTACT ───────────────────────────────────────────────
    cluster_leader_name  = Column(String(100), nullable=True)
    cluster_leader_phone = Column(String(20), nullable=True)
    cluster_leader_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    # Links to a registered User who leads this cluster

    # ── METADATA ──────────────────────────────────────────────
    is_active       = Column(Boolean, default=True, nullable=False)
    notes           = Column(Text, nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────
    created_at      = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at      = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # ── RELATIONSHIPS ─────────────────────────────────────────
    cluster_leader  = relationship("User", foreign_keys=[cluster_leader_user_id])

    def __repr__(self):
        return (
            f"<FisherCluster {self.cluster_code} "
            f"{self.name} "
            f"members={self.members_count} "
            f"status={self.cluster_status}>"
        )