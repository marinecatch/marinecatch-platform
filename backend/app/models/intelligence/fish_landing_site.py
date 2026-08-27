# app/models/intelligence/fish_landing_site.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class FishLandingSite(Base, ProvenanceMixin):
    __tablename__ = "fish_landing_sites"

    id                       = Column(Integer, primary_key=True)
    official_name            = Column(String(200), nullable=False, index=True)
    local_name                 = Column(String(200), nullable=True)
    county_id                    = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    sub_county_id                   = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    ward_id                            = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    locality_id                           = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    bmu_id                                   = Column(Integer, ForeignKey("bmus.id"), nullable=True)

    latitude                                    = Column(Float, nullable=True)
    longitude                                      = Column(Float, nullable=True)

    gazetted_status                                   = Column(String(30), default="UNKNOWN")
    operational_status                                   = Column(String(30), default="UNKNOWN")
    landing_type                                            = Column(String(50), nullable=True)
    marine_environment                                         = Column(String(50), nullable=True)
    beach_type                                                    = Column(String(50), nullable=True)

    estimated_fisher_count                                          = Column(Integer, nullable=True)
    estimated_boat_count                                               = Column(Integer, nullable=True)
    estimated_daily_volume_kg                                             = Column(Float, nullable=True)
    infrastructure_grade                                                     = Column(String(20), nullable=True)

    cold_storage_available    = Column(Boolean, nullable=True)
    ice_available              = Column(Boolean, nullable=True)
    electricity_available        = Column(Boolean, nullable=True)
    water_available                = Column(Boolean, nullable=True)
    road_access                       = Column(Boolean, nullable=True)
    road_condition                       = Column(String(30), nullable=True)
    boat_repair                             = Column(Boolean, nullable=True)
    gear_repair                                = Column(Boolean, nullable=True)
    fish_banda                                    = Column(Boolean, nullable=True)
    toilets                                          = Column(Boolean, nullable=True)
    fish_processing                                     = Column(Boolean, nullable=True)
    fish_drying                                            = Column(Boolean, nullable=True)
    waste_management                                          = Column(Boolean, nullable=True)
    market_access                                                = Column(Boolean, nullable=True)
    mobile_network                                                  = Column(Boolean, nullable=True)
    internet_connectivity                                              = Column(Boolean, nullable=True)
    land_tenure_status                                                     = Column(String(30), nullable=True)
    site_classification                                                        = Column(String(300), nullable=True)
    is_island            = Column(Boolean, nullable=True)

    bmu = relationship("BMU", back_populates="landing_sites")

    def __repr__(self):
        return f"<FishLandingSite {self.official_name}>"