# app/api/v1/routes/fish.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.fish import FishListingCreate, FishSpecies, LandingSite
from app.database.memory_store import (
    create_listing, get_all_listings, get_listing_by_id
)

router = APIRouter(prefix="/fish", tags=["Fish Listings"])

@router.get("/")
def browse_listings(
    species: Optional[FishSpecies] = Query(None),
    landing_site: Optional[LandingSite] = Query(None)
):
    """
    Browse available fish.
    Neptune Hotels can filter by species=lobster.
    Samaki Samaki can filter by landing_site=kibuyuni.
    """
    return get_all_listings(
        species=species.value if species else None,
        landing_site=landing_site.value if landing_site else None
    )

@router.get("/{listing_id}")
def get_listing(listing_id: int):
    """Get one listing with full details."""
    listing = get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404,
                           detail="Listing not found")
    return listing

@router.post("/", status_code=201)
def create_fish_listing(listing: FishListingCreate):
    """
    Fisher creates a new catch listing.
    Example: Abdalla Masudi lists 40kg octopus from Kibuyuni.
    Auth required — added Day 5.
    """
    return create_listing({
        "fisher_id":    1,
        "fisher_name":  "Abdalla Masudi",
        "species":      listing.species.value,
        "weight_kg":    listing.weight_kg,
        "price_per_kg": listing.price_per_kg,
        "landing_site": listing.landing_site.value,
        "condition":    listing.condition.value,
        "description":  listing.description,
        "harvest_date": listing.harvest_date,
        "boat_number":  listing.boat_number,
    })