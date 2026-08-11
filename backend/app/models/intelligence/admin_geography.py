# app/models/intelligence/admin_geography.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class AdminGeography(Base, ProvenanceMixin):
    """
    Generic self-referencing administrative tree.
    country_code always populated. geography_type is an open vocabulary
    string, not a fixed enum. Kenya: county/sub_county/ward/locality.
    Another country's hierarchy needs no schema change, only new rows.
    """
    __tablename__ = "admin_geography"

    id                  = Column(Integer, primary_key=True)
    parent_id           = Column(Integer, ForeignKey("admin_geography.id"), nullable=True)
    country_code        = Column(String(3), nullable=False, index=True)
    geography_type       = Column(String(50), nullable=False, index=True)
    official_name         = Column(String(200), nullable=False)
    administrative_code     = Column(String(50), nullable=True)
    centroid_latitude         = Column(Float, nullable=True)
    centroid_longitude          = Column(Float, nullable=True)
    effective_from                = Column(DateTime(timezone=True), nullable=True)
    effective_to                     = Column(DateTime(timezone=True), nullable=True)
    is_active                           = Column(String(10), default="true")

    children = relationship("AdminGeography", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<AdminGeography {self.geography_type}:{self.official_name}>"