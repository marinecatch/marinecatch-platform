from sqlalchemy import Column, Integer, Float, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base
from .provenance import ProvenanceMixin


class SpeciesGearAssociation(Base, ProvenanceMixin):
    """
    Reference relationship between a species and fishing gear.

    Stores gear/species targeting and selectivity intelligence.
    Provenance fields are supplied by ProvenanceMixin.
    """

    __tablename__ = "species_gear_associations"

    id                = Column(Integer, primary_key=True)
    species_id        = Column(Integer, ForeignKey("species.id"), nullable=False)
    fishing_gear_id   = Column(Integer, ForeignKey("fishing_gears.id"), nullable=False)

    is_primary_target = Column(Boolean, nullable=True)
    selectivity_score = Column(Float, nullable=True)
    bycatch_risk      = Column(String(20), nullable=True)

    species = relationship(
        "Species",
        back_populates="gear_associations",
    )

    fishing_gear = relationship(
        "FishingGear",
        back_populates="species_associations",
    )

    def __repr__(self):
        return (
            f"<SpeciesGearAssociation "
            f"species={self.species_id} gear={self.fishing_gear_id}>"
        )