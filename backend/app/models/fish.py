# app/models/fish.py
#
# WHY THIS FILE EXISTS:
# Defines the fish_listings table in PostgreSQL.
# Every catch listed on the marketplace is stored here.
#
# Real examples:
# Bakari Usi lists 85kg yellowfin tuna from Kibuyuni
# Hassan Juma lists 25kg live oysters from Ukunda
# Shee Sahare lists 18kg live crab from Mwambao

from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class FishCondition(str, enum.Enum):
    FRESH     = "fresh"
    FROZEN    = "frozen"
    DRIED     = "dried"
    PROCESSED = "processed"
    LIVE      = "live"

class FishListing(Base):
    __tablename__ = "fish_listings"

    id              = Column(Integer, primary_key=True, index=True)
    fisher_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    species         = Column(String(50), nullable=False, index=True)
    weight_kg       = Column(Float, nullable=False)
    available_kg    = Column(Float, nullable=False)
    price_per_kg    = Column(Float, nullable=False)
    total_value_kes = Column(Float, nullable=False)
    landing_site    = Column(String(50), nullable=False, index=True)
    condition       = Column(SAEnum(FishCondition), default=FishCondition.FRESH)
    description     = Column(Text, nullable=True)
    harvest_date    = Column(String(20), nullable=True)
    boat_number     = Column(String(50), nullable=True)
    is_available    = Column(Boolean, default=True, nullable=False, index=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    fisher = relationship("User", back_populates="listings")
    orders = relationship("Order", back_populates="listing")

    def __repr__(self):
        return f"<FishListing id={self.id} species={self.species} weight={self.weight_kg}kg>"