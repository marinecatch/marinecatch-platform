# app/models/intelligence/fisheries_observation.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class FisheriesObservation(Base, ProvenanceMixin):
    """
    Generic fisheries statistical fact — frame counts (sites, fishers,
    vessels), catch tonnage, production value, at region/district
    level, annual or monthly. Deliberately generic and currency-aware
    so it works for any country going forward. Conflicting figures
    from the same or different sources are preserved as separate
    rows (is_canonical distinguishes preferred vs alternative),
    never overwritten.
    """
    __tablename__ = "fisheries_observations"

    id                 = Column(Integer, primary_key=True)
    admin_geography_id = Column(Integer, ForeignKey("admin_geography.id"), nullable=False)
    metric_type        = Column(String(40), nullable=False)
    # landing_site_count | fisher_count | vessel_count |
    # catch_tonnes | production_value | inboard_engines |
    # outboard_engines | vessel_type_count
    metric_subtype     = Column(String(50), nullable=True)
    # e.g. vessel type name (ngalawa, mashua) when metric_type=vessel_type_count
    value               = Column(Float, nullable=True)
    currency            = Column(String(3), nullable=True)  # null for non-monetary metrics
    period_year         = Column(Integer, nullable=True)
    period_month        = Column(Integer, nullable=True)     # null = annual
    frame_reference_year = Column(Integer, nullable=True)    # e.g. 2018 frame reported in 2020
    is_canonical        = Column(String(10), default="false")
    # matches the GeographySourceClaim is_canonical string-bool convention

    def __repr__(self):
        return f"<FisheriesObservation {self.metric_type}={self.value} year={self.period_year}>"