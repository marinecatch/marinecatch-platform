# app/models/intelligence/geographic_alias.py
from sqlalchemy import Column, Integer, String
from app.database.connection import Base


class GeographicAlias(Base):
    """
    Alternate spellings/names for any geography or fisheries entity.
    Kiromo / Chiromo / Koromo -> one canonical entity, multiple aliases.
    Never auto-merge; aliases require human review and confidence rating.
    """
    __tablename__ = "geographic_aliases"

    id                  = Column(Integer, primary_key=True)
    entity_type         = Column(String(50), nullable=False)
    canonical_entity_id = Column(Integer, nullable=False)
    alias_name          = Column(String(200), nullable=False)
    source_id           = Column(Integer, nullable=True)
    source_year         = Column(Integer, nullable=True)
    confidence          = Column(String(20), default="MEDIUM")

    def __repr__(self):
        return f"<GeographicAlias {self.alias_name} -> {self.entity_type}:{self.canonical_entity_id}>"