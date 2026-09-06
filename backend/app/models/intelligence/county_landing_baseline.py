# app/models/intelligence/county_landing_baseline.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base


class CountyLandingBaseline(Base):
    """
    Annual quantitative fisheries production baseline per county,
    from KeFS statistical bulletins. First structured volume/value
    data point feeding the future Species/Price/Market Intelligence layer.
    """
    __tablename__ = "county_landing_baselines"

    id                   = Column(Integer, primary_key=True)
    admin_geography_id    = Column(Integer, ForeignKey("admin_geography.id"), nullable=False)
    year                     = Column(Integer, nullable=False)
    total_tonnes                = Column(Float, nullable=True)
    total_value_kes                = Column(Float, nullable=True)
    demersal_tonnes                   = Column(Float, nullable=True)
    pelagic_tonnes                       = Column(Float, nullable=True)
    shark_ray_tonnes                        = Column(Float, nullable=True)
    crustacean_tonnes                          = Column(Float, nullable=True)
    misc_tonnes                                   = Column(Float, nullable=True)
    source_id                                        = Column(Integer, nullable=True)
    source_name                                          = Column(String(255), nullable=True)
    verification_status                                     = Column(String(30), nullable=False, default="RESEARCH_SOURCE")
    created_at                                                 = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CountyLandingBaseline {self.admin_geography_id} {self.year}: {self.total_tonnes}t>"