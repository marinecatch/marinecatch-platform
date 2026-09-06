# app/models/intelligence/ecological_zone.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class EcologicalZone(Base, ProvenanceMixin):
    """
    Seagrass beds, mangroves, reefs, turtle foraging areas, MPAs, creeks.
    Distinct from FishingGround (an operational area fishers use) —
    this is the habitat/protection layer above it.
    """
    __tablename__ = "ecological_zones"

    id                = Column(Integer, primary_key=True)
    name              = Column(String(200), nullable=False)
    zone_type         = Column(String(50), nullable=True)
    # seagrass | mangrove | reef | turtle_foraging | mpa | creek
    landing_site_id     = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    fishing_ground_id      = Column(Integer, ForeignKey("fishing_grounds.id"), nullable=True)
    protection_status         = Column(String(50), nullable=True)
    area_km2                     = Column(Float, nullable=True)

    def __repr__(self):
        return f"<EcologicalZone {self.name} ({self.zone_type})>"