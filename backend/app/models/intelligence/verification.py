# app/models/intelligence/verification.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.database.connection import Base


class FieldVerification(Base):
    __tablename__ = "field_verifications"
    id                    = Column(Integer, primary_key=True)
    landing_site_id         = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=False)
    verification_status       = Column(String(30), nullable=False, default="UNVERIFIED")
    gps_latitude                 = Column(Float, nullable=True)
    gps_longitude                   = Column(Float, nullable=True)
    photo_url                          = Column(String(500), nullable=True)
    verified_by_name                      = Column(String(150), nullable=True)
    verified_boat_count                      = Column(Integer, nullable=True)
    verified_fisher_count                       = Column(Integer, nullable=True)
    notes                                          = Column(Text, nullable=True)
    verified_at                                       = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FieldVerification site={self.landing_site_id} status={self.verification_status}>"


class SiteCommercialScore(Base):
    __tablename__ = "site_commercial_scores"
    id                        = Column(Integer, primary_key=True)
    landing_site_id             = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=False)
    supply_volume_score            = Column(Float, nullable=True)
    species_diversity_score           = Column(Float, nullable=True)
    high_value_species_score             = Column(Float, nullable=True)
    buyer_demand_score                      = Column(Float, nullable=True)
    cold_chain_score                           = Column(Float, nullable=True)
    logistics_access_score                        = Column(Float, nullable=True)
    fisher_density_score                             = Column(Float, nullable=True)
    data_quality_score                                  = Column(Float, nullable=True)
    sustainability_risk_score                              = Column(Float, nullable=True)
    composite_score                                           = Column(Float, nullable=True)
    computed_at                                                  = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<SiteCommercialScore site={self.landing_site_id} score={self.composite_score}>"


class SiteInvestmentScore(Base):
    __tablename__ = "site_investment_scores"
    id                  = Column(Integer, primary_key=True)
    landing_site_id       = Column(Integer, ForeignKey("fish_landing_sites.id"), nullable=False)
    category                 = Column(String(50), nullable=False)
    priority_rank                = Column(Integer, nullable=True)
    estimated_cost_kes              = Column(Float, nullable=True)
    rationale                          = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SiteInvestmentScore site={self.landing_site_id} category={self.category}>"