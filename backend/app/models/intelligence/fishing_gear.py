# app/models/intelligence/fishing_gear.py
from sqlalchemy import Column, Integer, String, Float
from app.database.connection import Base
from .provenance import ProvenanceMixin


class FishingGear(Base, ProvenanceMixin):
    """
    Gear tracked as a proper entity (not free text), per Lamu package
    section 17 — supports future compliance/traceability/selectivity scoring.
    """
    __tablename__ = "fishing_gears"

    id                = Column(Integer, primary_key=True)
    name              = Column(String(150), nullable=False)
    local_name        = Column(String(150), nullable=True)
    gear_category     = Column(String(100), nullable=True)
    target_species    = Column(String(300), nullable=True)
    prohibited_status = Column(String(30), nullable=True)
    selectivity_score = Column(Float, nullable=True)
    environmental_risk = Column(String(30), nullable=True)
    permitted_area    = Column(String(200), nullable=True)
    seasonality       = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<FishingGear {self.name}>"