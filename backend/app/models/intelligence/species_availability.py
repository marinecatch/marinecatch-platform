# app/models/intelligence/species_availability.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class SpeciesAvailability(Base, ProvenanceMixin):
    __tablename__ = "species_availability"
    id                  = Column(Integer, primary_key=True)
    landing_site_id       = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=False)
    species_id               = Column(Integer, ForeignKey("species.id"), nullable=True)
    species_name_raw            = Column(String(150), nullable=True)
    average_volume_kg               = Column(Float, nullable=True)
    peak_volume_kg                     = Column(Float, nullable=True)
    minimum_volume_kg                     = Column(Float, nullable=True)
    catch_frequency                          = Column(String(50), nullable=True)
    catch_method                                = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<SpeciesAvailability site={self.landing_site_id} species={self.species_name_raw}>"


class SpeciesSeasonality(Base, ProvenanceMixin):
    __tablename__ = "species_seasonality"
    id                       = Column(Integer, primary_key=True)
    species_availability_id    = Column(Integer, ForeignKey("species_availability.id"), nullable=False)
    month                         = Column(Integer, nullable=False)
    expected_availability            = Column(Integer, nullable=True)
    confidence                          = Column(String(20), default="LOW")
    historical_basis                       = Column(String(200), nullable=True)
    observed_date                             = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<SpeciesSeasonality month={self.month} availability={self.expected_availability}>"