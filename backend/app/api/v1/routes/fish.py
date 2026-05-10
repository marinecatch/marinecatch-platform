# app/api/v1/routes/fish.py
#
# PROTECTED ENDPOINTS:
# POST /fish — fishers only (requires JWT token)
# GET /fish  — public (anyone can browse)
#
# Real scenario:
# Abdalla Masudi logs in → gets token → creates listing
# Neptune Hotels browses without token → sees all listings

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.schemas.fish import FishListingCreate, FishSpecies, LandingSite
from app.database.memory_store import (
    create_listing,
    get_all_listings,
    get_listing_by_id
)
from app.api.v1.routes.users import get_current_user

router = APIRouter(prefix="/fish", tags=["Fish Listings"])

# ── PUBLIC — anyone can browse ────────────────────────────────────
@router.get("/")
def browse_listings(
    species: Optional[FishSpecies] = Query(None),
    landing_site: Optional[LandingSite] = Query(None)
):
    """
    Browse all available fish listings.
    Public endpoint — no login required.

    Examples:
    /api/v1/fish                        → all listings
    /api/v1/fish?species=tuna           → tuna only
    /api/v1/fish?landing_site=kibuyuni  → Kibuyuni catch only
    """
    return get_all_listings(
        species=species.value if species else None,
        landing_site=landing_site.value if landing_site else None
    )

@router.get("/{listing_id}")
def get_listing(listing_id: int):
    """Get one listing. Public — no login required."""
    listing = get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )
    return listing

# ── PROTECTED — fishers only ──────────────────────────────────────
@router.post("/", status_code=201)
def create_fish_listing(
    listing: FishListingCreate,
    current_user: dict = Depends(get_current_user)  # ← requires token
):
    """
    Create a new fish listing.
    REQUIRES: Login token + fisher role.

    Example:
    Abdalla Masudi logs in, posts 40kg octopus from Kibuyuni.
    Neptune Hotels tries → gets 403 Forbidden.
    """
    # Role check — only fishers and suppliers can list fish
    if current_user["role"] not in ["fisher", "supplier"]:
        raise HTTPException(
            status_code=403,
            detail=f"Only fishers and suppliers can create listings. Your role: {current_user['role']}"
        )

    return create_listing({
        "fisher_id":    current_user["id"],
        "fisher_name":  current_user["name"],
        "species":      listing.species.value,
        "weight_kg":    listing.weight_kg,
        "price_per_kg": listing.price_per_kg,
        "landing_site": listing.landing_site.value,
        "condition":    listing.condition.value,
        "description":  listing.description,
        "harvest_date": listing.harvest_date,
        "boat_number":  listing.boat_number,
    })

@router.delete("/{listing_id}")
def remove_listing(
    listing_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a listing.
    Only the fisher who created it can remove it.
    """
    from app.database.memory_store import update_listing

    listing = get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only owner can delete
    if listing["fisher_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="You can only remove your own listings"
        )

    update_listing(listing_id, {"is_available": False})
    return {"message": f"Listing {listing_id} removed successfully"}