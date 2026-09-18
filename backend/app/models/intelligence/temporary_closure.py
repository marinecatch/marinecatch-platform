# app/models/intelligence/temporary_closure.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class TemporaryClosure(Base, ProvenanceMixin):
    """
    Time-bound, community-managed fishing closures (e.g. octopus
    closures / TURFs common in Zanzibar). Distinct from
    MarineManagementArea (permanent) — this is scheduled/rotational.
    """
    __tablename__ = "temporary_closures"

    id                 = Column(Integer, primary_key=True)
    name               = Column(String(200), nullable=False)
    landing_site_id    = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    fishing_ground_id  = Column(Integer, ForeignKey("fishing_grounds.id"), nullable=True)
    closure_type       = Column(String(50), nullable=True)   # octopus_closure | turf | seasonal_ban | other
    target_species     = Column(String(200), nullable=True)  # free text, e.g. "octopus"
    opens_date         = Column(Date, nullable=True)
    closes_date        = Column(Date, nullable=True)
    is_recurring       = Column(String(10), nullable=True)   # "true"/"false" — matches existing string-bool pattern
    governing_body      = Column(String(200), nullable=True) # e.g. "Kiwengwa Shehia Fisheries Committee"

    def __repr__(self):
        return f"<TemporaryClosure {self.name} type={self.closure_type}>"