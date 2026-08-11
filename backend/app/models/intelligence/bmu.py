# app/models/intelligence/bmu.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class BMU(Base, ProvenanceMixin):
    """
    Beach Management Unit. Distinct from FishLandingSite:
    one BMU manages MANY landing sites.
    Example: Kibuyuni BMU manages Kibuyuni, Kijiweni, Ngomani,
    Kiromo, Huawen, Mtibwani landing sites.
    """
    __tablename__ = "bmus"

    id                     = Column(Integer, primary_key=True)
    official_name          = Column(String(200), nullable=False, index=True)
    county_id               = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    sub_county_id             = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    ward_id                     = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    headquarters_location         = Column(String(200), nullable=True)
    registration_status              = Column(String(50), nullable=True)
    active_status                       = Column(String(30), default="UNKNOWN")
    membership_count                       = Column(Integer, nullable=True)
    fisher_count                              = Column(Integer, nullable=True)
    boat_count                                   = Column(Integer, nullable=True)
    trader_count                                    = Column(Integer, nullable=True)
    women_members                                      = Column(Integer, nullable=True)
    youth_members                                         = Column(Integer, nullable=True)
    governance_status                                        = Column(String(100), nullable=True)
    contact_person                                              = Column(String(150), nullable=True)
    contact_phone                                                  = Column(String(30), nullable=True)
    contact_email                                                     = Column(String(150), nullable=True)

    landing_sites = relationship("FishLandingSite", back_populates="bmu")

    def __repr__(self):
        return f"<BMU {self.official_name}>"