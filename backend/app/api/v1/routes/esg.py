# app/api/v1/routes/esg.py
#
# WHY THIS FILE EXISTS:
# ESG and traceability endpoints.
# Fisheries intelligence infrastructure exposed over HTTP.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.esg_service import (
    log_catch_event,
    generate_traceability_chain,
    get_species_sustainability,
    check_species_export_eligibility,
    get_or_create_fisher_impact_profile,
    update_fisher_impact_metrics,
    get_esg_dashboard,
)
from app.models.esg import SpeciesSustainabilityProfile

router = APIRouter(prefix="/esg", tags=["ESG & Traceability"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class CatchEventCreate(BaseModel):
    fisher_id:              int
    species:                str
    weight_kg:              float
    landing_site:           str
    lot_id:                 Optional[int]   = None
    catch_method:           Optional[str]   = None
    gear_type:              Optional[str]   = None
    vessel_reg:             Optional[str]   = None
    vessel_name:            Optional[str]   = None
    vessel_size_category:   Optional[str]   = None
    crew_size:              Optional[int]   = None
    female_crew_count:      Optional[int]   = None
    trip_duration_days:     Optional[float] = None
    fishing_ground:         Optional[str]   = None
    gps_lat_catch:          Optional[float] = None
    gps_lng_catch:          Optional[float] = None
    bmu_reference:          Optional[str]   = None
    landing_officer:        Optional[str]   = None
    fishing_permit_no:      Optional[str]   = None
    permit_expiry_date:     Optional[str]   = None
    is_cross_border:        bool            = False
    origin_country:         str             = "KE"
    temperature_at_landing: Optional[float] = None
    ice_used:               Optional[bool]  = None
    ice_kg:                 Optional[float] = None
    individual_count:       Optional[int]   = None
    scientific_name:        Optional[str]   = None
    notes:                  Optional[str]   = None


# ── CATCH EVENTS ──────────────────────────────────────────────────

@router.post("/catch", status_code=201)
def create_catch_event(
    payload:     CatchEventCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Log a catch/landing event.
    Called by fisher, BMU officer, or MarineCatch staff.
    Auto-assesses IUU risk based on available data.
    """
    event = log_catch_event(db=db, **payload.model_dump())
    return {
        "success":        True,
        "catch_event_id": event.id,
        "species":        event.species,
        "weight_kg":      event.weight_kg,
        "landing_site":   event.landing_site,
        "iuu_risk_level": event.iuu_risk_level,
        "iuu_risk_notes": event.iuu_risk_notes,
        "catch_timestamp": event.catch_timestamp,
        "message":        f"Catch event logged. IUU risk: {event.iuu_risk_level.value}"
    }


# ── TRACEABILITY ──────────────────────────────────────────────────

@router.post("/trace/{order_id}")
def create_traceability_chain(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Generate full traceability chain for an order.
    Connects catch → lot → order → shipment → buyer.
    Used for export compliance and buyer transparency.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    chain = generate_traceability_chain(
        db=order_id and db,
        order_id=order_id,
        generated_by=current_user.name,
    )
    return {
        "chain_reference":      chain.chain_reference,
        "order_id":             chain.order_id,
        "fisher_name":          chain.fisher_name,
        "landing_site":         chain.landing_site,
        "catch_date":           chain.catch_date,
        "species":              chain.species,
        "quantity_kg":          chain.quantity_kg,
        "buyer_name":           chain.buyer_name,
        "iuu_risk_level":       chain.iuu_risk_level,
        "cold_chain_maintained": chain.cold_chain_maintained,
        "permits_verified":     chain.permits_verified,
        "bmu_verified":         chain.bmu_verified,
        "export_ready":         chain.export_ready,
        "export_issues":        chain.export_issues,
    }


# ── SPECIES ───────────────────────────────────────────────────────

@router.get("/species")
def list_species(
    db: Session = Depends(get_db),
):
    """All species sustainability profiles. Public."""
    profiles = db.query(SpeciesSustainabilityProfile).order_by(
        SpeciesSustainabilityProfile.species_name
    ).all()
    return [
        {
            "species_name":        p.species_name,
            "scientific_name":     p.scientific_name,
            "local_names":         p.local_names,
            "sustainability":      p.sustainability_status,
            "sassi_rating":        p.sassi_rating,
            "iucn_status":         p.iucn_status,
            "minimum_size_cm":     p.minimum_size_cm,
            "export_permitted":    p.export_permitted,
            "requires_permit":     p.requires_permit,
            "closed_season_start": p.closed_season_start,
            "closed_season_end":   p.closed_season_end,
            "typical_price_range_kes": p.typical_price_range_kes,
        }
        for p in profiles
    ]


@router.get("/species/{species_name}/export-check")
def species_export_check(
    species_name: str,
    gear_type:    Optional[str] = Query(None),
    db: Session   = Depends(get_db),
):
    """
    Check if a species is eligible for export.
    Used before generating compliance documents.
    """
    return check_species_export_eligibility(db, species_name, gear_type)


# ── FISHER IMPACT ─────────────────────────────────────────────────

@router.get("/fisher/{fisher_id}/impact")
def get_fisher_impact(
    fisher_id:   int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Fisher ESG impact profile.
    Fisher sees own profile. Admin sees any.
    """
    if current_user.role != "admin" and current_user.id != fisher_id:
        raise HTTPException(status_code=403, detail="Access denied")

    profile = get_or_create_fisher_impact_profile(db, fisher_id)
    return {
        "fisher_id":              profile.fisher_id,
        "lifetime_catch_kg":      profile.lifetime_catch_kg,
        "lifetime_earnings_kes":  profile.lifetime_earnings_kes,
        "total_transactions":     profile.total_transactions,
        "primary_species":        profile.primary_species,
        "bmu_name":               profile.bmu_name,
        "cooperative_name":       profile.cooperative_name,
        "owns_vessel":            profile.owns_vessel,
        "has_smartphone":         profile.has_smartphone,
        "has_life_jacket":        profile.has_life_jacket,
        "profile_complete":       profile.profile_complete,
        "last_updated_at":        profile.last_updated_at,
    }


@router.post("/fisher/{fisher_id}/impact/refresh")
def refresh_fisher_impact(
    fisher_id:   int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Recompute fisher impact metrics from transaction history."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    profile = update_fisher_impact_metrics(db, fisher_id)
    return {
        "success":                True,
        "fisher_id":              fisher_id,
        "lifetime_catch_kg":      profile.lifetime_catch_kg,
        "lifetime_earnings_kes":  profile.lifetime_earnings_kes,
        "total_transactions":     profile.total_transactions,
        "primary_species":        profile.primary_species,
    }


# ── ESG DASHBOARD ─────────────────────────────────────────────────

@router.get("/dashboard")
def esg_dashboard(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Platform-wide ESG impact summary.
    Used by admin, investors, ESG reporters, grant applications.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_esg_dashboard(db)