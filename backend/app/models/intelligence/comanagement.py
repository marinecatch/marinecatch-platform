# app/models/intelligence/comanagement.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin

bmu_jcma = Table(
    "bmu_jcma", Base.metadata,
    Column("bmu_id", Integer, ForeignKey("bmus.id"), primary_key=True),
    Column("jcma_id", Integer, ForeignKey("jcm_as.id"), primary_key=True),
)


class JointCoManagementArea(Base, ProvenanceMixin):
    __tablename__ = "jcm_as"
    id          = Column(Integer, primary_key=True)
    name         = Column(String(200), nullable=False)
    description    = Column(String(500), nullable=True)

    bmus = relationship("BMU", secondary=bmu_jcma)

    def __repr__(self):
        return f"<JointCoManagementArea {self.name}>"


mma_bmu = Table(
    "mma_bmu", Base.metadata,
    Column("mma_id", Integer, ForeignKey("marine_management_areas.id"), primary_key=True),
    Column("bmu_id", Integer, ForeignKey("bmus.id"), primary_key=True),
)


class MarineManagementArea(Base, ProvenanceMixin):
    """LMMAs. Explicitly not the same entity as a BMU or JCMA."""
    __tablename__ = "marine_management_areas"

    id                  = Column(Integer, primary_key=True)
    designation           = Column(String(200), nullable=False)
    status                  = Column(String(30), nullable=True)
    year_established           = Column(Integer, nullable=True)
    area_km2                      = Column(Float, nullable=True)
    no_take_status                   = Column(String(10), nullable=True)
    management_authority                = Column(String(200), nullable=True)

    bmus = relationship("BMU", secondary=mma_bmu)

    def __repr__(self):
        return f"<MarineManagementArea {self.designation}>"