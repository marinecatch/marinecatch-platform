# app/models/intelligence/logistics_graph.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.connection import Base
from .provenance import ProvenanceMixin


class LogisticsNode(Base, ProvenanceMixin):
    __tablename__ = "logistics_nodes"
    id             = Column(Integer, primary_key=True)
    landing_site_id  = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    node_type          = Column(String(50), nullable=False)
    name                  = Column(String(200), nullable=False)

    def __repr__(self):
        return f"<LogisticsNode {self.name}>"


class SupplyCorridor(Base, ProvenanceMixin):
    """Conceptual until validated by real logistics data."""
    __tablename__ = "supply_corridors"
    id     = Column(Integer, primary_key=True)
    name    = Column(String(200), nullable=False)
    status   = Column(String(20), default="potential")
    # observed | potential | pilot | validated

    def __repr__(self):
        return f"<SupplyCorridor {self.name} status={self.status}>"


class SupplyCorridorNode(Base):
    __tablename__ = "supply_corridor_nodes"
    id                  = Column(Integer, primary_key=True)
    corridor_id           = Column(Integer, ForeignKey("supply_corridors.id"), nullable=False)
    landing_site_id          = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=True)
    node_name                   = Column(String(200), nullable=True)
    sequence_order                 = Column(Integer, nullable=False)
    distance_km                       = Column(Float, nullable=True)
    estimated_travel_time_min            = Column(Integer, nullable=True)
    transport_cost_kes                      = Column(Float, nullable=True)
    refrigeration_required                     = Column(String(10), nullable=True)
    road_quality                                  = Column(String(30), nullable=True)
    seasonal_accessibility                           = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<SupplyCorridorNode #{self.sequence_order} corridor={self.corridor_id}>"