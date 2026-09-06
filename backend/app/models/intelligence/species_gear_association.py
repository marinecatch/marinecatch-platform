from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from .provenance import ProvenanceMixin


class SpeciesProcessingProfile(Base, ProvenanceMixin):
    __tablename__ = "species_processing_profiles"

    id                     = Column(Integer, primary_key=True)
    species_id             = Column(Integer, ForeignKey("species.id"), nullable=False)
    product_form           = Column(String(30), nullable=False)
    yield_percentage       = Column(Float, nullable=True)
    typical_loss_pct       = Column(Float, nullable=True)
    shelf_life_days_iced   = Column(Float, nullable=True)
    shelf_life_days_frozen = Column(Float, nullable=True)
    handling_notes         = Column(Text, nullable=True)

    species = relationship("Species", back_populates="processing_profiles")

    def __repr__(self):
        return f"<SpeciesProcessingProfile species={self.species_id} form={self.product_form}>"