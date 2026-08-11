# app/models/intelligence/provenance.py
#
# Shared provenance columns applied to reference/research tables only.
# Never applied to operational tables (InventoryLot, Order, etc.)

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func


class ProvenanceMixin:
    """
    Every geography/fisheries intelligence record carries these fields.
    verification_status values:
    VERIFIED_OFFICIAL | VERIFIED_MULTI_SOURCE | OFFICIAL_UNVERIFIED |
    RESEARCH_SOURCE | COMMUNITY_REPORTED | SECONDARY_SOURCE |
    CONFLICTING | HISTORICAL | NEEDS_FIELD_VERIFICATION
    """
    source_id           = Column(Integer, nullable=True)
    source_name         = Column(String(255), nullable=True)
    source_year         = Column(Integer, nullable=True)
    source_page         = Column(String(50), nullable=True)
    source_text         = Column(Text, nullable=True)
    verification_status = Column(String(30), nullable=False, default="RESEARCH_SOURCE")
    last_verified_at    = Column(DateTime(timezone=True), nullable=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())