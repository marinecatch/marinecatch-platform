# app/models/quality_inspection.py
#
# WHY THIS FILE EXISTS:
# A catch should NOT automatically become a marketplace listing.
# Every InventoryLot goes through an inspection before it can be
# sold to institutional buyers.
#
# Lot pipeline:
# logged → pending_inspection → passed → available → reserved → sold
#                             → rejected → disposition
#
# A rejected lot is NEVER deleted. It remains in the database
# with its lot number permanently reserved. This is how
# traceability systems work.
#
# Rejection dispositions:
# MARKETPLACE      — passed, listed for sale
# DIRECT_SALE      — sold directly without marketplace listing
# PROCESSING_ONLY  — can only go to processor, not retail
# RETURN_TO_FISHER — quality too low, returned
# ANIMAL_FEED      — downgraded to feed
# DISPOSED         — unsafe, destroyed
# DONATED          — given to community

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, ForeignKey, Enum, Text)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum


class InspectionStatus(str, enum.Enum):
    PENDING      = "pending"
    PASSED       = "passed"
    FAILED       = "failed"
    CONDITIONAL  = "conditional"   # Passed with conditions


class InspectionGrade(str, enum.Enum):
    A        = "A"    # Premium — hotels, export
    B        = "B"    # Good — restaurants, processors
    C        = "C"    # Acceptable — local market only
    REJECTED = "R"    # Failed inspection


class LotDisposition(str, enum.Enum):
    MARKETPLACE       = "marketplace"        # Standard listing
    DIRECT_SALE       = "direct_sale"        # Sold directly
    PROCESSING_ONLY   = "processing_only"    # Processor only
    RETURN_TO_FISHER  = "return_to_fisher"   # Returned
    ANIMAL_FEED       = "animal_feed"        # Downgraded
    DISPOSED          = "disposed"           # Destroyed
    DONATED           = "donated"            # Community


class QualityInspection(Base):
    __tablename__ = "quality_inspections"

    id               = Column(Integer, primary_key=True, index=True)
    lot_id           = Column(Integer, ForeignKey("inventory_lots.id"),
                              unique=True, nullable=False, index=True)
    inspector_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspector_name   = Column(String(100), nullable=True)

    # ── INSPECTION RESULT ─────────────────────────────────────────
    status           = Column(Enum(InspectionStatus),
                              default=InspectionStatus.PENDING)
    grade            = Column(Enum(InspectionGrade), nullable=True)
    disposition      = Column(Enum(LotDisposition), nullable=True)

    # ── QUALITY CHECKS ────────────────────────────────────────────
    temperature_c        = Column(Float, nullable=True)
    temperature_ok       = Column(Boolean, nullable=True)
    # Should be ≤4°C for fresh, ≤-18°C for frozen

    smell_ok             = Column(Boolean, nullable=True)
    texture_ok           = Column(Boolean, nullable=True)
    appearance_ok        = Column(Boolean, nullable=True)
    ice_ratio_ok         = Column(Boolean, nullable=True)
    gills_ok             = Column(Boolean, nullable=True)    # For whole fish
    eyes_ok              = Column(Boolean, nullable=True)    # Clear vs cloudy

    # ── WEIGHT VERIFICATION ───────────────────────────────────────
    declared_weight_kg   = Column(Float, nullable=True)
    verified_weight_kg   = Column(Float, nullable=True)
    weight_variance_kg   = Column(Float, nullable=True)
    # If variance > 5%, flag for review

    # ── REJECTION ────────────────────────────────────────────────
    rejection_reason     = Column(Text, nullable=True)
    # Temperature abuse, spoilage, wrong species, underweight,
    # IUU suspicion, damaged packaging

    # ── CONDITIONAL PASS ─────────────────────────────────────────
    conditions           = Column(Text, nullable=True)
    # e.g. "Must be sold within 24 hours", "Processing only"

    # ── NOTES ────────────────────────────────────────────────────
    notes                = Column(Text, nullable=True)
    photos_taken         = Column(Boolean, default=False)
    photo_urls           = Column(Text, nullable=True)
    # comma-separated S3 URLs when we add photo upload

    # ── TIMESTAMPS ───────────────────────────────────────────────
    inspected_at         = Column(DateTime(timezone=True), nullable=True)
    created_at           = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime(timezone=True),
                                 onupdate=lambda: datetime.now(timezone.utc))

    # ── RELATIONSHIPS ────────────────────────────────────────────
    inspector            = relationship("User", foreign_keys=[inspector_id])