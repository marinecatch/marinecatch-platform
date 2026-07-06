# app/models/catch_draft.py
#
# WHY THIS FILE EXISTS:
# A catch reported by a fisher is NOT inventory yet.
# CatchDraft captures the fisher's submission before
# quality inspection and MarineCatch acceptance.
#
# Pipeline:
# CatchDraft (submitted) → Quality Inspection → InventoryLot
#
# A rejected draft never becomes inventory.
# The draft remains permanently for audit trail.
# Lot numbers are only assigned after acceptance.
#
# Price distinction:
# asking_price_per_kg  = fisher's requested price
# selling_price_per_kg = MarineCatch's market price (set after inspection)
#                        includes commission, cold chain, logistics

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, ForeignKey, Text)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class CatchDraftStatus:
    AWAITING_PRICE     = "awaiting_price"
    SUBMITTED          = "submitted"
    UNDER_INSPECTION   = "under_inspection"
    ACCEPTED           = "accepted"
    REJECTED           = "rejected"
    CANCELLED          = "cancelled"


class CatchDraft(Base):
    __tablename__ = "catch_drafts"

    id                   = Column(Integer, primary_key=True, index=True)
    reference_number     = Column(String(30), unique=True, nullable=False, index=True)
    # Format: MC-DRAFT-20260705-0001

    # ── FISHER ───────────────────────────────────────────────────
    fisher_id            = Column(Integer, ForeignKey("users.id"), nullable=False)
    fisher_name          = Column(String(100), nullable=True)
    fisher_phone         = Column(String(20), nullable=True)
    cluster_id           = Column(Integer, ForeignKey("fisher_clusters.id"), nullable=True)
    member_id            = Column(String(20), nullable=True)
    # MC-FSH-000001

    # ── CATCH DETAILS ─────────────────────────────────────────────
    species              = Column(String(50), nullable=True)
    weight_kg            = Column(Float, nullable=True)
    landing_site         = Column(String(100), nullable=True)
    catch_date           = Column(DateTime(timezone=True), nullable=True)
    gear_type            = Column(String(50), nullable=True)
    vessel_registration  = Column(String(50), nullable=True)

    # ── PRICING ───────────────────────────────────────────────────
    asking_price_per_kg  = Column(Float, nullable=True)
    # Fisher's requested price — what they want to receive

    # ── CHANNEL ───────────────────────────────────────────────────
    submission_channel   = Column(String(20), default="whatsapp")
    # whatsapp, ussd, web, app

    # ── STATUS ────────────────────────────────────────────────────
    status               = Column(String(30), default=CatchDraftStatus.AWAITING_PRICE)

    # ── INSPECTION ────────────────────────────────────────────────
    quality_grade        = Column(String(2), nullable=True)
    inspection_notes     = Column(Text, nullable=True)
    inspected_by         = Column(String(100), nullable=True)
    inspected_at         = Column(DateTime(timezone=True), nullable=True)
    rejection_reason     = Column(Text, nullable=True)

    # ── CONVERSION ────────────────────────────────────────────────
    created_inventory_lot_id = Column(Integer,
                                      ForeignKey("inventory_lots.id"),
                                      nullable=True)
    # Set when draft is accepted and converted to InventoryLot

    # ── PHOTO ─────────────────────────────────────────────────────
    photo_url            = Column(String(500), nullable=True)
    # Phase 2 — S3 URL of catch photo

    # ── GPS ───────────────────────────────────────────────────────
    latitude             = Column(Float, nullable=True)
    longitude            = Column(Float, nullable=True)
    # Phase 2

    # ── NOTES ─────────────────────────────────────────────────────
    notes                = Column(Text, nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────────
    submitted_at         = Column(DateTime(timezone=True), nullable=True)
    accepted_at          = Column(DateTime(timezone=True), nullable=True)
    created_at           = Column(DateTime(timezone=True),
                                  default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime(timezone=True),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # ── RELATIONSHIPS ─────────────────────────────────────────────
    fisher               = relationship("User", foreign_keys=[fisher_id])