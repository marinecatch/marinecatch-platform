# app/models/intelligence/shehia_fisheries_committee.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin

sfc_jcma = Table(
    "sfc_jcma", Base.metadata,
    Column("sfc_id", Integer, ForeignKey("shehia_fisheries_committees.id"), primary_key=True),
    Column("jcma_id", Integer, ForeignKey("jcm_as.id"), primary_key=True),
)


class ShehiaFisheriesCommittee(Base, ProvenanceMixin):
    """
    Zanzibar's community-level fisheries governance institution —
    structurally parallel to BMU (one SFC -> many landing sites)
    but deliberately kept as its own table. Never rename as BMU.
    Membership: ~10 elected marine-resource users per SFC.
    """
    __tablename__ = "shehia_fisheries_committees"

    id                = Column(Integer, primary_key=True)
    name              = Column(String(200), nullable=False, index=True)
    alternate_name    = Column(String(200), nullable=True)  # e.g. historical "VFC" usage
    shehia_id         = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    formation_year     = Column(Integer, nullable=True)
    active_status         = Column(String(30), default="UNKNOWN")
    cmg_affiliation_status   = Column(String(30), nullable=True)
    # "affiliated" | "unaffiliated_confirmed" | "unknown" —
    # distinguishes "confirmed not in a CMG" from "not yet researched"

    landing_sites = relationship("FishLandingSite", back_populates="sfc")
    cmgs          = relationship("JointCoManagementArea", secondary=sfc_jcma)

    def __repr__(self):
        return f"<ShehiaFisheriesCommittee {self.name}>"