# app/models/intelligence/temporary_closure.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from app.database.connection import Base
from .provenance import ProvenanceMixin


class TemporaryClosure(Base, ProvenanceMixin):
    """
    Generic spatial/temporal closure — octopus closures, seasonal
    nursery closures, replenishment areas, breeding-area closures,
    emergency closures. Deliberately species-agnostic and
    multi-parent: any one (or more) of the FK fields may be set
    depending on what governs/hosts the closure. Distinct from
    MarineManagementArea (permanent) — this is scheduled/rotational.
    """
    __tablename__ = "temporary_closures"

    id                  = Column(Integer, primary_key=True)
    name                = Column(String(200), nullable=False)
    closure_type        = Column(String(50), nullable=True)
    # octopus_closure | seasonal_nursery | replenishment_area |
    # breeding_area | emergency | other
    status              = Column(String(30), default="UNKNOWN")
    # proposed | active | reopened | lapsed | unknown

    start_date          = Column(Date, nullable=True)
    end_date            = Column(Date, nullable=True)
    reopen_date         = Column(Date, nullable=True)

    target_species_id   = Column(Integer, ForeignKey("species.id"), nullable=True)
    landing_site_id      = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    fishing_ground_id       = Column(Integer, ForeignKey("fishing_grounds.id"), nullable=True)
    management_area_id         = Column(Integer, ForeignKey("management_areas.id"), nullable=True)
    marine_management_area_id     = Column(Integer, ForeignKey("marine_management_areas.id"), nullable=True)
    governing_sfc_id                 = Column(Integer, ForeignKey("shehia_fisheries_committees.id"), nullable=True)
    governing_cmg_id                    = Column(Integer, ForeignKey("jcm_as.id"), nullable=True)

    geometry_note                          = Column(Text, nullable=True)
    # free-text/GeoJSON placeholder — real geometry type deferred
    # until PostGIS need is confirmed (per earlier architecture note)

    def __repr__(self):
        return f"<TemporaryClosure {self.name} type={self.closure_type} status={self.status}>"