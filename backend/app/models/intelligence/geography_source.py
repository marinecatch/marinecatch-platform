# app/models/intelligence/geography_source.py
from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base


class GeographySource(Base):
    """Tier-ranked source registry. Every claim traces back here."""
    __tablename__ = "geography_sources"

    id                   = Column(Integer, primary_key=True)
    title                = Column(String(300), nullable=False)
    issuing_organization = Column(String(200), nullable=True)
    publication_year     = Column(Integer, nullable=True)
    document_type        = Column(String(100), nullable=True)
    geographic_scope     = Column(String(150), nullable=True)
    source_url           = Column(String(500), nullable=True)
    reliability_tier     = Column(Integer, nullable=False)
    extracted_date       = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<GeographySource {self.title} tier={self.reliability_tier}>"


class GeographySourceClaim(Base):
    """
    Polymorphic claim table. Conflicting facts from different sources
    are both preserved here rather than one overwriting the other.
    """
    __tablename__ = "geography_source_claims"

    id           = Column(Integer, primary_key=True)
    entity_type  = Column(String(50), nullable=False)
    entity_id    = Column(Integer, nullable=True)
    claim_field  = Column(String(100), nullable=False)
    claim_value  = Column(Text, nullable=False)
    source_id    = Column(Integer, nullable=False)
    is_canonical = Column(String(10), default="false")
    notes        = Column(Text, nullable=True)

    def __repr__(self):
        return f"<GeographySourceClaim {self.entity_type}.{self.claim_field}={self.claim_value}>"