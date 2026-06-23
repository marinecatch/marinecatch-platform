# app/models/fisheries_data.py
#
# WHY THIS FILE EXISTS:
# BMU landing data from Kibuyuni Beach Management Unit.
# Data collected for Kenya Fisheries Service, 2024-2025.
# Used for: market intelligence, price analytics,
# species seasonality, supply forecasting, procurement planning.
#
# IMPORTANT: This data belongs to the BMU/KFS.
# MarineCatch uses it with permission for analytics only.
# Not to be resold or claimed as proprietary.
#
# Models:
# Species         — species registry with local names
# LandingSite     — formal landing site registry
# HistoricalLanding — monthly BMU catch records

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class FishCategory(str, enum.Enum):
    DEMERSAL    = "demersal"    # Bottom-dwelling: Tafi, Changgu, Tembo
    PELAGIC     = "pelagic"     # Open water: Kole Kole, Barracuda, Nguru
    CRUSTACEAN  = "crustacean"  # Prawns, Lobster, Crab
    MOLLUSC     = "mollusc"     # Octopus, Squid
    ELASMOBRANCH = "elasmobranch" # Sharks, Rays
    OTHER       = "other"


# ── SPECIES ───────────────────────────────────────────────────────

class Species(Base):
    __tablename__ = "species"

    id              = Column(Integer, primary_key=True, index=True)
    common_name     = Column(String(100), nullable=False, index=True)
    # English: Rabbit Fish, Scavenger, Snapper

    scientific_name = Column(String(150), nullable=True)
    # Siganidae, Lethrinidae, Lutjanidae

    local_name      = Column(String(100), nullable=True, index=True)
    # Swahili: Tafi, Changgu, Tembo, Kole Kole, Pweza

    family          = Column(String(100), nullable=True)
    # Siganidae, Lethrinidae, etc.

    category        = Column(
        SAEnum(FishCategory, name="fishcategory", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=FishCategory.DEMERSAL
    )

    # Pricing intelligence
    avg_price_per_kg_kes    = Column(Float, nullable=True)
    min_price_per_kg_kes    = Column(Float, nullable=True)
    max_price_per_kg_kes    = Column(Float, nullable=True)
    # Updated by analytics job from historical data

    # Seasonality
    peak_months     = Column(String(50), nullable=True)
    # "9,10,11" = September, October, November peak

    # Sustainability
    iucn_status     = Column(String(50), nullable=True)
    # LC, NT, VU, EN, CR — IUCN Red List status

    is_active       = Column(Boolean, default=True, nullable=False)
    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Species {self.common_name} ({self.local_name})>"


# ── LANDING SITE ──────────────────────────────────────────────────

class LandingSite(Base):
    __tablename__ = "landing_sites"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False, index=True)
    # Kibuyuni, Shimoni, Vanga, Mwambao, Majoreni

    code            = Column(String(20), unique=True, nullable=False)
    # KBY, SHM, VNG, MWB, MJR

    bmu_name        = Column(String(100), nullable=True)
    # Beach Management Unit name

    bmu_registration = Column(String(50), nullable=True)
    county          = Column(String(50), nullable=True)
    # Kwale, Mombasa, Kilifi

    sub_county      = Column(String(50), nullable=True)
    gps_lat         = Column(Float, nullable=True)
    gps_lng         = Column(Float, nullable=True)

    # Capacity
    active_fishers  = Column(Integer, nullable=True)
    active_vessels  = Column(Integer, nullable=True)

    is_active       = Column(Boolean, default=True, nullable=False)
    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<LandingSite {self.code} — {self.name}>"


# ── HISTORICAL LANDING ────────────────────────────────────────────

class HistoricalLanding(Base):
    __tablename__ = "historical_landings"

    id              = Column(Integer, primary_key=True, index=True)

    # Time period
    year            = Column(Integer, nullable=False, index=True)
    month           = Column(Integer, nullable=False, index=True)
    # 1=January, 12=December

    # Location
    landing_site_id = Column(Integer, ForeignKey("landing_sites.id"), nullable=True)
    landing_site_name = Column(String(100), nullable=True)
    # Denormalized for easy querying

    # Species
    species_id      = Column(Integer, ForeignKey("species.id"), nullable=True)
    species_common  = Column(String(100), nullable=False)
    species_local   = Column(String(100), nullable=True)
    species_family  = Column(String(100), nullable=True)
    category        = Column(String(20), nullable=True)
    # demersal, pelagic, crustacean, mollusc

    # Volume and value
    weight_kg       = Column(Float, nullable=False)
    value_kes       = Column(Float, nullable=True)
    price_per_kg    = Column(Float, nullable=True)
    # Calculated: value_kes / weight_kg

    # Data source
    data_source     = Column(String(100), nullable=True)
    # "Kibuyuni BMU — KFS Record"

    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    landing_site    = relationship("LandingSite", foreign_keys=[landing_site_id])
    species         = relationship("Species", foreign_keys=[species_id])

    def __repr__(self):
        return (
            f"<HistoricalLanding {self.year}-{self.month:02d} "
            f"{self.species_common} {self.weight_kg}kg>"
        )