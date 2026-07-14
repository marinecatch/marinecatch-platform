# app/models/storage_node.py
#
# WHY THIS FILE EXISTS:
# Cold storage as a network of nodes MarineCatch coordinates
# rather than owns. Kibuyuni BMU, Kinondo BMU, Alpha Logistics
# facilities, and future Tatu City SEZ storage all become
# nodes in this network.

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        DateTime, Text, ForeignKey)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class StorageNode(Base):
    __tablename__ = "storage_nodes"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(150), nullable=False)
    operator_name       = Column(String(150), nullable=True)
    # "Kinondo BMU", "Kibuyuni BMU", "Alpha Logistics"

    location            = Column(String(150), nullable=True)
    county              = Column(String(50), nullable=True)

    # ── CAPACITY ──────────────────────────────────────────────
    capacity_kg         = Column(Float, nullable=True)
    available_kg        = Column(Float, nullable=True)

    # ── INFRASTRUCTURE ────────────────────────────────────────
    power_source        = Column(String(20), nullable=True)
    # solar, grid, hybrid
    has_backup_power    = Column(Boolean, default=False)
    has_ice_machine     = Column(Boolean, default=False)
    temperature_c       = Column(Float, nullable=True)
    is_certified        = Column(Boolean, default=False)
    has_aluminium_shelves = Column(Boolean, default=False)

    # ── COMMERCIAL TERMS ──────────────────────────────────────
    cost_model          = Column(String(30), default="informal")
    # per_kg_per_night, flat_rate, informal
    cost_rate_kes       = Column(Float, nullable=True)
    access_terms        = Column(Text, nullable=True)
    # free text: "Informal, chairman approval required"

    # ── PARTNER LINK ──────────────────────────────────────────
    partner_id          = Column(Integer,
                                 ForeignKey("logistics_partners.id"),
                                 nullable=True)
    # If third-party owned (Alpha, future partners)

    # ── IOT ────────────────────────────────────────────────────
    iot_sensor_id       = Column(String(50), nullable=True)

    is_active           = Column(Boolean, default=True)
    notes               = Column(Text, nullable=True)

    created_at          = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True),
                                 onupdate=lambda: datetime.now(timezone.utc))

    partner             = relationship("LogisticsPartner", foreign_keys=[partner_id])