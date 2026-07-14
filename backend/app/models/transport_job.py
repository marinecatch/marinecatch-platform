# app/models/transport_job.py
#
# WHY THIS FILE EXISTS:
# One shipment, many jobs. A lot moving from Kibuyuni to
# Nairobi involves: motorbike to Ukunda stage, bus to Nairobi,
# rider for last-mile delivery — three separate TransportJobs
# under one logical shipment.
#
# This mirrors the real operational flow described by the
# founder: multiple providers, multiple legs, one journey.

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, Text, ForeignKey)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class TransportJob(Base):
    __tablename__ = "transport_jobs"

    id                  = Column(Integer, primary_key=True, index=True)
    shipment_id         = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    # Groups jobs that belong to the same overall journey
    sequence_number     = Column(Integer, default=1)
    # 1st leg, 2nd leg, 3rd leg

    order_id            = Column(Integer, ForeignKey("orders.id"), nullable=True)
    lot_id              = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)

    pickup_location      = Column(String(150), nullable=True)
    destination_location = Column(String(150), nullable=True)

    partner_id          = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True)
    cooler_asset_id      = Column(Integer, ForeignKey("cooler_assets.id"), nullable=True)

    job_type            = Column(String(20), nullable=True)
    # first_mile, long_haul, last_mile, return

    status              = Column(String(20), default="pending")
    # pending, in_transit, completed, delayed, failed

    scheduled_departure = Column(DateTime(timezone=True), nullable=True)
    actual_departure    = Column(DateTime(timezone=True), nullable=True)
    scheduled_arrival    = Column(DateTime(timezone=True), nullable=True)
    actual_arrival       = Column(DateTime(timezone=True), nullable=True)

    cost_kes            = Column(Float, nullable=True)
    payment_status       = Column(String(20), default="unpaid")
    # unpaid, paid, disputed

    tracking_reference  = Column(String(100), nullable=True)
    # bus ticket number, courier tracking number

    temperature_at_pickup   = Column(Float, nullable=True)
    temperature_at_delivery = Column(Float, nullable=True)

    exception_notes      = Column(Text, nullable=True)
    notes                = Column(Text, nullable=True)

    created_at           = Column(DateTime(timezone=True),
                                  default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime(timezone=True),
                                  onupdate=lambda: datetime.now(timezone.utc))

    partner              = relationship("LogisticsPartner", foreign_keys=[partner_id])