from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class SpeciesMarketPrice(Base, ProvenanceMixin):
    __tablename__ = "species_market_prices"

    id              = Column(Integer, primary_key=True)
    species_id      = Column(Integer, ForeignKey("species.id"), nullable=False)
    market_tier     = Column(String(20), nullable=False)
    currency        = Column(String(3), default="KES", nullable=False)
    price_min       = Column(Float, nullable=True)
    price_max       = Column(Float, nullable=True)
    price_avg       = Column(Float, nullable=True)
    unit            = Column(String(20), default="per_kg", nullable=True)
    observed_period = Column(String(50), nullable=True)

    species = relationship("Species", back_populates="market_prices")

    def __repr__(self):
        return f"<SpeciesMarketPrice species={self.species_id} tier={self.market_tier}>"