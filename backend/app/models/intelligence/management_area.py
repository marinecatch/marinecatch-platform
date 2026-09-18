# app/models/intelligence/management_area.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin

management_area_sfc = Table(
    "management_area_sfc", Base.metadata,
    Column("management_area_id", Integer, ForeignKey("management_areas.id"), primary_key=True),
    Column("sfc_id", Integer, ForeignKey("shehia_fisheries_committees.id"), primary_key=True),
)


class ManagementArea(Base, ProvenanceMixin):
    """
    The rung between a MarineManagementArea (e.g. PECCA) and the
    SFCs within it. E.g. PECCA Zone 5, PECCA Zone 6,
    'Management Area No. 3'. NOT the same as a CMG — this is a
    spatial subdivision of an MCA, not a cross-cutting governance
    coordination body.
    """
    __tablename__ = "management_areas"

    id                        = Column(Integer, primary_key=True)
    name                      = Column(String(200), nullable=False)
    marine_management_area_id = Column(Integer, ForeignKey("marine_management_areas.id"), nullable=False)
    zone_number               = Column(String(20), nullable=True)
    description               = Column(String(500), nullable=True)

    sfcs = relationship("ShehiaFisheriesCommittee", secondary=management_area_sfc)

    def __repr__(self):
        return f"<ManagementArea {self.name}>"