# app/api/v1/routes/intelligence.py
#
# Read-only geography/species intelligence endpoints. No write
# routes yet — deliberate, per the referential-integrity concern
# on entity_type/entity_id (GeographySourceClaim) raised before
# any admin write surface gets built.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.connection import get_db
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.shehia_fisheries_committee import ShehiaFisheriesCommittee
from app.models.intelligence.comanagement import MarineManagementArea, JointCoManagementArea
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.fisheries_observation import FisheriesObservation
from app.models.intelligence.infrastructure import InfrastructureAsset
from app.models.intelligence.species_market_price import SpeciesMarketPrice
from app.models.fisheries_data import Species

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ── GEOGRAPHY ──────────────────────────────────────────────────────

@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    rows = db.query(AdminGeography.country_code).distinct().all()
    return {"countries": [r[0] for r in rows]}


@router.get("/admin-geography")
def list_admin_geography(
    country: str = Query(..., description="ISO country_code, e.g. KEN, TZA"),
    geography_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(AdminGeography).filter(AdminGeography.country_code == country)
    if geography_type:
        q = q.filter(AdminGeography.geography_type == geography_type)
    if parent_id is not None:
        q = q.filter(AdminGeography.parent_id == parent_id)
    rows = q.order_by(AdminGeography.official_name).all()
    return {
        "admin_geography": [
            {
                "id": r.id, "name": r.official_name, "type": r.geography_type,
                "parent_id": r.parent_id, "verification_status": r.verification_status,
                "source_name": r.source_name,
            }
            for r in rows
        ]
    }


@router.get("/admin-geography/tree")
def admin_geography_tree(country: str = Query(...), db: Session = Depends(get_db)):
    """Full hierarchy for one country, nested."""
    all_nodes = db.query(AdminGeography).filter(AdminGeography.country_code == country).all()
    by_id = {n.id: {"id": n.id, "name": n.official_name, "type": n.geography_type,
                     "children": []} for n in all_nodes}
    roots = []
    for n in all_nodes:
        node = by_id[n.id]
        if n.parent_id and n.parent_id in by_id:
            by_id[n.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return {"tree": roots}


@router.get("/landing-sites")
def list_landing_sites(
    bmu_id: Optional[int] = None,
    county_id: Optional[int] = None,
    verification_status: Optional[str] = None,
    site_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(FishLandingSite)
    if bmu_id:
        q = q.filter(FishLandingSite.bmu_id == bmu_id)
    if county_id:
        q = q.filter(FishLandingSite.county_id == county_id)
    if verification_status:
        q = q.filter(FishLandingSite.verification_status == verification_status)
    if site_type:
        q = q.filter(FishLandingSite.site_type == site_type)
    if search:
        q = q.filter(FishLandingSite.official_name.ilike(f"%{search}%"))
    total = q.count()
    rows = q.order_by(FishLandingSite.official_name).offset(offset).limit(limit).all()
    return {
        "total": total,
        "landing_sites": [
            {
                "id": r.id, "name": r.official_name, "local_name": r.local_name,
                "site_type": r.site_type, "bmu_id": r.bmu_id,
                "latitude": r.latitude, "longitude": r.longitude,
                "verification_status": r.verification_status,
                "confidence_score": r.confidence_score,
                "operational_status": r.operational_status,
                "site_classification": r.site_classification,
            }
            for r in rows
        ],
    }


@router.get("/landing-sites/{site_id}")
def get_landing_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(FishLandingSite).filter(FishLandingSite.id == site_id).first()
    if not site:
        raise HTTPException(404, "Landing site not found")

    bmu = db.query(BMU).filter(BMU.id == site.bmu_id).first() if site.bmu_id else None
    sfc = db.query(ShehiaFisheriesCommittee).filter(ShehiaFisheriesCommittee.id == site.sfc_id).first() if getattr(site, "sfc_id", None) else None
    infra = db.query(InfrastructureAsset).filter(InfrastructureAsset.landing_site_id == site.id).all()
    claims = db.query(GeographySourceClaim).filter(
        GeographySourceClaim.entity_type == "fish_landing_site",
        GeographySourceClaim.entity_id == site.id,
    ).all()

    return {
        "id": site.id,
        "name": site.official_name,
        "local_name": site.local_name,
        "site_type": site.site_type,
        "site_role": site.site_role,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "environment_type": site.environment_type,
        "operational_status": site.operational_status,
        "verification_status": site.verification_status,
        "data_verification_stage": site.data_verification_stage,
        "confidence_score": site.confidence_score,
        "site_classification": site.site_classification,
        "land_tenure_status": site.land_tenure_status,
        "bmu": {"id": bmu.id, "name": bmu.official_name} if bmu else None,
        "sfc": {"id": sfc.id, "name": sfc.name} if sfc else None,
        "infrastructure": [
            {"id": i.id, "asset_type": i.asset_type, "operational_status": i.operational_status,
             "funding_program": i.funding_program, "financier": i.financier}
            for i in infra
        ],
        "source_name": site.source_name,
        "claims": [
            {"field": c.claim_field, "value": c.claim_value, "is_canonical": c.is_canonical}
            for c in claims
        ],
    }


@router.get("/bmus")
def list_bmus(country: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(BMU)
    rows = q.order_by(BMU.official_name).all()
    result = []
    for r in rows:
        site_count = db.query(func.count(FishLandingSite.id)).filter(FishLandingSite.bmu_id == r.id).scalar()
        result.append({
            "id": r.id, "name": r.official_name, "active_status": r.active_status,
            "verification_status": r.verification_status, "landing_site_count": site_count,
        })
    return {"bmus": result}


@router.get("/marine-management-areas")
def list_mmas(db: Session = Depends(get_db)):
    rows = db.query(MarineManagementArea).order_by(MarineManagementArea.designation).all()
    return {
        "marine_management_areas": [
            {"id": r.id, "designation": r.designation, "year_established": r.year_established,
             "area_km2": r.area_km2, "verification_status": r.verification_status}
            for r in rows
        ]
    }


# ── SPECIES ────────────────────────────────────────────────────────

@router.get("/species")
def list_species(search: Optional[str] = None, category: Optional[str] = None,
                  db: Session = Depends(get_db)):
    q = db.query(Species)
    if search:
        q = q.filter(Species.common_name.ilike(f"%{search}%"))
    if category:
        q = q.filter(Species.category == category)
    rows = q.order_by(Species.common_name).all()
    return {
        "species": [
            {
                "id": r.id, "common_name": r.common_name, "scientific_name": r.scientific_name,
                "family": r.family, "category": r.category, "iucn_status": r.iucn_status,
                "verification_status": r.verification_status, "confidence_score": r.confidence_score,
            }
            for r in rows
        ]
    }


@router.get("/species/{species_id}")
def get_species_detail(species_id: int, db: Session = Depends(get_db)):
    sp = db.query(Species).filter(Species.id == species_id).first()
    if not sp:
        raise HTTPException(404, "Species not found")

    prices = db.query(SpeciesMarketPrice).filter(SpeciesMarketPrice.species_id == sp.id).all()
    claims = db.query(GeographySourceClaim).filter(
        GeographySourceClaim.entity_type == "species",
        GeographySourceClaim.entity_id == sp.id,
    ).all()

    return {
        "id": sp.id, "common_name": sp.common_name, "scientific_name": sp.scientific_name,
        "family": sp.family, "order": sp.order, "category": sp.category,
        "iucn_status": sp.iucn_status, "cites_appendix": sp.cites_appendix,
        "eu_catch_cert_required": sp.eu_catch_cert_required,
        "min_legal_size_cm": sp.min_legal_size_cm,
        "verification_status": sp.verification_status,
        "confidence_score": sp.confidence_score,
        "source_name": sp.source_name,
        "notes": sp.notes,
        "market_prices": [
            {"tier": p.market_tier, "currency": p.currency, "avg": p.price_avg,
             "min": p.price_min, "max": p.price_max, "period": p.observed_period}
            for p in prices
        ],
        "claims": [
            {"field": c.claim_field, "value": c.claim_value, "is_canonical": c.is_canonical}
            for c in claims
        ],
    }


# ── DATA QUALITY / SUMMARY ────────────────────────────────────────

@router.get("/data-quality")
def data_quality_summary(country: Optional[str] = None, db: Session = Depends(get_db)):
    site_q = db.query(FishLandingSite)
    total_sites = site_q.count()

    def pct(numerator):
        return round(100 * numerator / total_sites, 1) if total_sites else 0

    verified = site_q.filter(FishLandingSite.verification_status.in_(
        ["VERIFIED_OFFICIAL", "VERIFIED_MULTI_SOURCE", "VERIFIED_SECONDARY"]
    )).count()
    with_coords = site_q.filter(FishLandingSite.latitude.isnot(None)).count()
    needs_verification = site_q.filter(
        FishLandingSite.verification_status.in_(["RESEARCH_SOURCE", "NEEDS_FIELD_VERIFICATION", "MAPPED"])
    ).count()

    total_bmus = db.query(func.count(BMU.id)).scalar()
    total_species = db.query(func.count(Species.id)).scalar()
    total_sources = db.query(func.count(GeographySource.id)).scalar()
    conflicting_claims = db.query(func.count(GeographySourceClaim.id)).filter(
        GeographySourceClaim.is_canonical == "false"
    ).scalar()

    return {
        "total_landing_sites": total_sites,
        "total_bmus": total_bmus,
        "total_species": total_species,
        "total_sources": total_sources,
        "pct_verified": pct(verified),
        "pct_with_coordinates": pct(with_coords),
        "needs_verification_count": needs_verification,
        "unreconciled_claims_count": conflicting_claims,
    }


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    rows = db.query(GeographySource).order_by(GeographySource.reliability_tier, GeographySource.title).all()
    return {
        "sources": [
            {"id": r.id, "title": r.title, "org": r.issuing_organization,
             "year": r.publication_year, "tier": r.reliability_tier}
            for r in rows
        ]
    }