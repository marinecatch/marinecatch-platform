# app/models/logistics_partner.py
#
# WHY THIS FILE EXISTS:
# MarineCatch coordinates logistics — it does not own trucks,
# coolers, or cold storage. Every rider, bus company, courier,
# fleet operator, or cold storage operator is a LogisticsPartner.
#
# This is the coordination layer's core registry — what each
# partner can actually do, where they operate, and how they
# perform over time.

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, Text)
from datetime import datetime, timezone
from app.database.connection import Base


class LogisticsPartner(Base):
    __tablename__ = "logistics_partners"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(150), nullable=False)
    partner_type        = Column(String(30), nullable=False)
    # individual_rider, bus_company, courier, fleet_operator,
    # cold_storage_operator, integrated_logistics_co

    contact_phone       = Column(String(20), nullable=True)
    contact_person      = Column(String(100), nullable=True)

    # ── COVERAGE ──────────────────────────────────────────────
    coverage_areas      = Column(Text, nullable=True)
    # comma-separated: "Ukunda,Nairobi,Diani"

    # ── CAPABILITIES ──────────────────────────────────────────
    cold_chain_capable  = Column(Boolean, default=False)
    max_payload_kg      = Column(Float, nullable=True)
    has_reefer          = Column(Boolean, default=False)
    temperature_range   = Column(String(50), nullable=True)
    # e.g. "-18 to 4"
    insurance_status    = Column(String(30), default="none")
    # none, basic, comprehensive
    export_certified    = Column(Boolean, default=False)
    has_api             = Column(Boolean, default=False)
    iot_compatible      = Column(Boolean, default=False)

    # ── COMMERCIAL TERMS ──────────────────────────────────────
    commission_model    = Column(String(20), default="flat_fee")
    # flat_fee, per_kg, tiered, percentage
    base_rate_kes       = Column(Float, nullable=True)
    per_km_rate_kes     = Column(Float, nullable=True)
    per_kg_rate_kes     = Column(Float, nullable=True)

    # ── SLA ────────────────────────────────────────────────────
    sla_pickup_hours    = Column(Float, nullable=True)
    sla_max_transit_hours = Column(Float, nullable=True)

    # ── PERFORMANCE (auto-updated) ────────────────────────────
    on_time_rate        = Column(Float, default=0.0)
    dispute_rate        = Column(Float, default=0.0)
    avg_rating          = Column(Float, default=0.0)
    total_jobs_completed = Column(Integer, default=0)

    # ── STATUS ────────────────────────────────────────────────
    is_active           = Column(Boolean, default=True)
    onboarded_at        = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))
    notes               = Column(Text, nullable=True)

    created_at          = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True),
                                 onupdate=lambda: datetime.now(timezone.utc))