# app/models/cooler_asset.py
#
# WHY THIS FILE EXISTS:
# MarineCatch manages physical assets, not just fish.
# Coolers move through the entire chain and can be lost,
# damaged, or delayed — like the Chania Genesis fire incident
# (2 coolers, KES 184,000, ongoing legal case).
#
# Tracking coolers as assets enables insurance claims,
# maintenance scheduling, and loss prevention.

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, Text)
from datetime import datetime, timezone
from app.database.connection import Base


class CoolerAsset(Base):
    __tablename__ = "cooler_assets"

    id                  = Column(Integer, primary_key=True, index=True)
    asset_code          = Column(String(30), unique=True, nullable=False, index=True)
    # MC-COOL-001

    capacity_kg         = Column(Float, nullable=True)
    owner               = Column(String(30), default="marinecatch")
    # marinecatch, partner_name

    status              = Column(String(20), default="available")
    # available, in_transit, at_storage, with_partner,
    # damaged, lost, retired

    current_holder      = Column(String(150), nullable=True)
    # free text or partner name
    current_location    = Column(String(150), nullable=True)

    iot_sensor_id       = Column(String(50), nullable=True)

    purchase_value_kes  = Column(Float, nullable=True)
    purchase_date       = Column(DateTime(timezone=True), nullable=True)

    incident_notes      = Column(Text, nullable=True)
    # For insurance/legal tracking — e.g. fire incident details

    created_at          = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True),
                                 onupdate=lambda: datetime.now(timezone.utc))