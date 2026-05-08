# app/schemas/fish.py
#
# WHY THIS FILE EXISTS:
# Defines what a fish listing looks like.
# Species list is based on actual Kenya/Western Indian Ocean fisheries.
# These are the species caught by your real fishers:
# - Abdalla Masudi catches octopus and snapper (Kibuyuni)
# - Hassan Juma Mwaropia catches oysters (Ukunda)
# - Shee Sahare catches crab (Mwambao)

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class FishSpecies(str, Enum):
    TUNA        = "tuna"
    OCTOPUS     = "octopus"
    SNAPPER     = "snapper"
    PRAWNS      = "prawns"
    LOBSTER     = "lobster"
    OYSTERS     = "oysters"
    CRAB        = "crab"
    SQUID       = "squid"
    KINGFISH    = "kingfish"
    RED_SNAPPER = "red_snapper"
    TILAPIA     = "tilapia"
    CATFISH     = "catfish"
    SARDINES    = "sardines"
    DRIED_FISH  = "dried_fish"
    OTHER       = "other"

class FishCondition(str, Enum):
    FRESH     = "fresh"
    FROZEN    = "frozen"
    DRIED     = "dried"
    PROCESSED = "processed"
    LIVE      = "live"       # Live oysters, live crab

class LandingSite(str, Enum):
    KIBUYUNI  = "kibuyuni"
    MAJORENI  = "majoreni"
    SHIMONI   = "shimoni"
    UKUNDA    = "ukunda"
    MWAMBAO   = "mwambao"
    VANGA     = "vanga"
    KINONDO   = "kinondo"
    MALINDI   = "malindi"
    LAMU      = "lamu"
    MOMBASA   = "mombasa"
    OTHER     = "other"

class FishListingCreate(BaseModel):
    species:       FishSpecies
    weight_kg:     float = Field(gt=0, le=5000)
    price_per_kg:  float = Field(gt=0)
    landing_site:  LandingSite
    condition:     FishCondition = FishCondition.FRESH
    description:   Optional[str] = Field(None, max_length=500)
    harvest_date:  Optional[str] = None   # "2025-05-07"
    boat_number:   Optional[str] = None   # BMU registration number

    @field_validator("weight_kg")
    @classmethod
    def round_weight(cls, v):
        return round(v, 2)

    @field_validator("price_per_kg")
    @classmethod
    def round_price(cls, v):
        return round(v, 2)

class FishListingResponse(BaseModel):
    id:              int
    fisher_id:       int
    fisher_name:     str
    species:         FishSpecies
    weight_kg:       float
    price_per_kg:    float
    total_value_kes: float
    landing_site:    LandingSite
    condition:       FishCondition
    description:     Optional[str]
    harvest_date:    Optional[str]
    boat_number:     Optional[str]
    is_available:    bool
    created_at:      datetime

    model_config = {"from_attributes": True}