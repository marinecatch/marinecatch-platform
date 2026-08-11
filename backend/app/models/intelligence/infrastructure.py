# app/models/intelligence/infrastructure.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class InfrastructureAsset(Base, ProvenanceMixin):
    __tablename__ = "infrastructure_assets"

    id                  = Column(Integer, primary_key=True)
    landing_site_id       = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=False)
    asset_type              = Column(String(50), nullable=False)
    capacity                   = Column(String(100), nullable=True)
    ownership                     = Column(String(50), nullable=True)
    operator                         = Column(String(150), nullable=True)
    operational_status                  = Column(String(30), default="UNKNOWN")
    installation_year                      = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<InfrastructureAsset {self.asset_type} @ site {self.landing_site_id}>"


class ColdChainAsset(Base, ProvenanceMixin):
    __tablename__ = "cold_chain_assets"

    id                  = Column(Integer, primary_key=True)
    landing_site_id       = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    asset_type              = Column(String(50), nullable=False)
    latitude                   = Column(Float, nullable=True)
    longitude                     = Column(Float, nullable=True)
    capacity_kg                      = Column(Float, nullable=True)
    temperature_range                   = Column(String(50), nullable=True)
    ownership                              = Column(String(50), nullable=True)
    operator                                  = Column(String(150), nullable=True)
    operational_status                           = Column(String(30), default="UNKNOWN")
    energy_source                                   = Column(String(50), nullable=True)
    species_supported                                  = Column(String(300), nullable=True)

    def __repr__(self):
        return f"<ColdChainAsset {self.asset_type}>"