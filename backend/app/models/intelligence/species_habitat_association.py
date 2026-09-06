from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class SpeciesHabitatAssociation(Base, ProvenanceMixin):
    __tablename__ = "species_habitat_associations"

    id                 = Column(Integer, primary_key=True)
    species_id         = Column(Integer, ForeignKey("species.id"), nullable=False)
    ecological_zone_id = Column(Integer, ForeignKey("ecological_zones.id"), nullable=False)

    species = relationship("Species", back_populates="habitat_associations")

    def __repr__(self):
        return f"<SpeciesHabitatAssociation species={self.species_id} zone={self.ecological_zone_id}>"