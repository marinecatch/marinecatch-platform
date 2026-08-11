# app/models/intelligence/market.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin

landing_site_markets = Table(
    "landing_site_markets", Base.metadata,
    Column("landing_site_id", Integer, ForeignKey("fish_landing_sites.id"), primary_key=True),
    Column("market_id", Integer, ForeignKey("markets.id"), primary_key=True),
)


class Market(Base, ProvenanceMixin):
    __tablename__ = "markets"
    id           = Column(Integer, primary_key=True)
    name          = Column(String(200), nullable=False)
    market_type     = Column(String(50), nullable=True)

    landing_sites = relationship("FishLandingSite", secondary=landing_site_markets)

    def __repr__(self):
        return f"<Market {self.name}>"