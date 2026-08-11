# app/models/intelligence/fishing_ground.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin

landing_site_fishing_grounds = Table(
    "landing_site_fishing_grounds", Base.metadata,
    Column("landing_site_id", Integer, ForeignKey("fish_landing_sites.id"), primary_key=True),
    Column("fishing_ground_id", Integer, ForeignKey("fishing_grounds.id"), primary_key=True),
)


class FishingGround(Base, ProvenanceMixin):
    """
    Explicitly NOT the same as a landing site.
    Fishers travel from a landing site to a fishing ground and back.
    """
    __tablename__ = "fishing_grounds"

    id                  = Column(Integer, primary_key=True)
    name                = Column(String(200), nullable=False)
    local_name             = Column(String(200), nullable=True)
    latitude                 = Column(Float, nullable=True)
    longitude                   = Column(Float, nullable=True)
    associated_bmu_id              = Column(Integer, ForeignKey("bmus.id"), nullable=True)
    habitat                           = Column(String(100), nullable=True)
    depth_range                          = Column(String(50), nullable=True)
    target_species                          = Column(String(300), nullable=True)
    gear_types                                 = Column(String(200), nullable=True)
    seasonal_usage                                = Column(String(100), nullable=True)
    fishing_pressure                                 = Column(String(30), nullable=True)
    protected_status                                    = Column(String(50), nullable=True)

    landing_sites = relationship("FishLandingSite", secondary=landing_site_fishing_grounds)

    def __repr__(self):
        return f"<FishingGround {self.name}>"