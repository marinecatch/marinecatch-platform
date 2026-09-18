# app/models/intelligence/governing_authority.py
from sqlalchemy import Column, Integer, String
from app.database.connection import Base
from .provenance import ProvenanceMixin


class GoverningAuthority(Base, ProvenanceMixin):
    """
    Distinguishes regulatory jurisdictions within or across a
    country_code — e.g. Zanzibar's semi-autonomous Department of
    Fisheries Development vs mainland Tanzania's fisheries authority.
    Referenced by AdminGeography and by governance entities so
    mainland/Zanzibar data is never silently conflated.
    """
    __tablename__ = "governing_authorities"

    id              = Column(Integer, primary_key=True)
    name            = Column(String(200), nullable=False)
    jurisdiction    = Column(String(50), nullable=False)
    # e.g. "zanzibar" | "mainland_tanzania" | "kenya_national"
    country_code    = Column(String(3), nullable=False)
    governance_type = Column(String(30), nullable=True)
    # CFMA | CMG | CMA | BMU_SYSTEM | other — the vocabulary itself,
    # not an instance of it

    def __repr__(self):
        return f"<GoverningAuthority {self.name} ({self.jurisdiction})>"