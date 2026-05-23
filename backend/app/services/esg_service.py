# app/services/esg_service.py
#
# WHY THIS FILE EXISTS:
# Fisheries intelligence service — the operational brain
# behind ESG reporting, traceability, and compliance.
#
# Key functions:
# - log_catch_event: record a landing event with full metadata
# - generate_traceability_chain: full catch-to-buyer chain
# - get_fisher_impact_profile: socioeconomic fisher data
# - get_species_sustainability: species compliance check
# - generate_compliance_document: flexible export document
# - get_esg_dashboard: platform-wide impact summary

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional

from app.models.esg import (
    CatchEvent, SpeciesSustainabilityProfile,
    FisherImpactProfile, TraceabilityChain,
    ComplianceDocument, IUURiskLevel,
    SustainabilityStatus, ComplianceDocType,
)
from app.models.inventory_lot import InventoryLot
from app.models.order import Order
from app.models.user import User
from app.models.logistics import Shipment
import json


# ── CATCH EVENT LOGGING ───────────────────────────────────────────

def log_catch_event(
    db:                    Session,
    fisher_id:             int,
    species:               str,
    weight_kg:             float,
    landing_site:          str,
    lot_id:                Optional[int]   = None,
    catch_method:          Optional[str]   = None,
    gear_type:             Optional[str]   = None,
    vessel_reg:            Optional[str]   = None,
    vessel_name:           Optional[str]   = None,
    vessel_size_category:  Optional[str]   = None,
    crew_size:             Optional[int]   = None,
    female_crew_count:     Optional[int]   = None,
    trip_duration_days:    Optional[float] = None,
    fishing_ground:        Optional[str]   = None,
    gps_lat_catch:         Optional[float] = None,
    gps_lng_catch:         Optional[float] = None,
    catch_timestamp:       Optional[datetime] = None,
    landing_timestamp:     Optional[datetime] = None,
    bmu_reference:         Optional[str]   = None,
    landing_officer:       Optional[str]   = None,
    fishing_permit_no:     Optional[str]   = None,
    permit_expiry_date:    Optional[str]   = None,
    is_cross_border:       bool            = False,
    origin_country:        str             = "KE",
    temperature_at_landing: Optional[float] = None,
    ice_used:              Optional[bool]  = None,
    ice_kg:                Optional[float] = None,
    individual_count:      Optional[int]   = None,
    scientific_name:       Optional[str]   = None,
    verified_by:           Optional[str]   = None,
    notes:                 Optional[str]   = None,
) -> CatchEvent:
    """
    Log a catch/landing event.
    Called when:
    - Fisher logs catch via WhatsApp/USSD/API
    - MarineCatch staff records landing
    - BMU officer verifies catch
    
    Auto-assesses IUU risk based on available data.
    """
    # Auto IUU risk assessment
    iuu_risk = IUURiskLevel.UNKNOWN
    iuu_notes = []

    if fishing_permit_no:
        iuu_risk = IUURiskLevel.LOW
    else:
        iuu_notes.append("No fishing permit recorded")
        iuu_risk = IUURiskLevel.MEDIUM

    if bmu_reference:
        if iuu_risk == IUURiskLevel.MEDIUM:
            iuu_risk = IUURiskLevel.LOW
    else:
        iuu_notes.append("No BMU reference")

    if is_cross_border and not fishing_permit_no:
        iuu_risk = IUURiskLevel.HIGH
        iuu_notes.append("Cross-border fisher without permit")

    event = CatchEvent(
        lot_id                        = lot_id,
        fisher_id                     = fisher_id,
        species                       = species.lower(),
        scientific_name               = scientific_name,
        weight_kg                     = weight_kg,
        individual_count              = individual_count,
        catch_method                  = catch_method,
        gear_type                     = gear_type,
        landing_site                  = landing_site.lower(),
        bmu_reference                 = bmu_reference,
        landing_officer               = landing_officer,
        catch_timestamp               = catch_timestamp or datetime.now(timezone.utc),
        landing_timestamp             = landing_timestamp or datetime.now(timezone.utc),
        fishing_ground                = fishing_ground,
        gps_lat_catch                 = gps_lat_catch,
        gps_lng_catch                 = gps_lng_catch,
        vessel_reg                    = vessel_reg,
        vessel_name                   = vessel_name,
        vessel_size_category          = vessel_size_category,
        crew_size                     = crew_size,
        trip_duration_days            = trip_duration_days,
        female_crew_count             = female_crew_count,
        fishing_permit_no             = fishing_permit_no,
        permit_expiry_date            = permit_expiry_date,
        is_cross_border               = is_cross_border,
        origin_country                = origin_country,
        iuu_risk_level                = iuu_risk,
        iuu_risk_notes                = " | ".join(iuu_notes) if iuu_notes else None,
        temperature_at_landing_celsius = temperature_at_landing,
        ice_used                      = ice_used,
        ice_kg                        = ice_kg,
        verified_by                   = verified_by,
        notes                         = notes,
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ── TRACEABILITY CHAIN GENERATOR ──────────────────────────────────

def generate_traceability_chain(
    db:       Session,
    order_id: int,
    generated_by: str = "system",
) -> TraceabilityChain:
    """
    Generate full traceability chain for an order.
    Connects: catch → lot → order → payment → shipment → buyer.
    
    This is the document that proves provenance.
    Used for: export compliance, buyer transparency, ESG reporting.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    buyer  = db.query(User).filter(User.id == order.buyer_id).first()
    fisher = db.query(User).filter(User.id == order.fisherman_id).first()
    lot    = db.query(InventoryLot).filter(
        InventoryLot.id == order.lot_id
    ).first() if order.lot_id else None

    # Find catch event linked to this lot
    catch_event = db.query(CatchEvent).filter(
        CatchEvent.lot_id == order.lot_id
    ).first() if order.lot_id else None

    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.order_id == order_id
    ).order_by(Shipment.created_at.desc()).first()

    # Generate reference
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = db.query(TraceabilityChain).filter(
        TraceabilityChain.chain_reference.like(f"MC-TRACE-{today}-%")
    ).count()
    ref = f"MC-TRACE-{today}-{str(count + 1).zfill(5)}"

    # Check for existing chain for this order
    existing = db.query(TraceabilityChain).filter(
        TraceabilityChain.order_id == order_id
    ).first()
    if existing:
        return existing

    # Assess compliance
    cold_chain_ok = True
    if shipment and shipment.cold_chain_status:
        cold_chain_ok = shipment.cold_chain_status.value != "breach"

    permits_ok = True
    if catch_event:
        permits_ok = catch_event.iuu_risk_level not in [
            IUURiskLevel.HIGH, IUURiskLevel.FLAGGED
        ]

    bmu_ok = bool(
        (lot and lot.bmu_reference) or
        (catch_event and catch_event.bmu_reference)
    )

    export_issues = []
    if not cold_chain_ok:
        export_issues.append("cold_chain_breach")
    if not permits_ok:
        export_issues.append("permit_issues")
    if not bmu_ok:
        export_issues.append("missing_bmu_reference")
    if not catch_event:
        export_issues.append("no_catch_event_logged")

    export_ready = len(export_issues) == 0

    chain = TraceabilityChain(
        chain_reference       = ref,
        order_id              = order_id,
        lot_id                = order.lot_id,
        catch_event_id        = catch_event.id if catch_event else None,
        shipment_id           = shipment.id if shipment else None,
        fisher_name           = fisher.name if fisher else None,
        fisher_id             = order.fisherman_id,
        landing_site          = order.landing_site,
        catch_date            = lot.catch_date if lot else None,
        species               = order.species,
        quantity_kg           = order.quantity_kg,
        buyer_name            = buyer.name if buyer else None,
        delivery_date         = shipment.actual_delivery_at.strftime("%Y-%m-%d")
                               if shipment and shipment.actual_delivery_at else None,
        iuu_risk_level        = catch_event.iuu_risk_level.value
                               if catch_event else "unknown",
        cold_chain_maintained = cold_chain_ok,
        permits_verified      = permits_ok,
        bmu_verified          = bmu_ok,
        export_ready          = export_ready,
        export_issues         = ",".join(export_issues) if export_issues else None,
    )

    db.add(chain)
    db.commit()
    db.refresh(chain)
    return chain


# ── SPECIES SUSTAINABILITY CHECK ──────────────────────────────────

def get_species_sustainability(
    db:      Session,
    species: str,
) -> Optional[SpeciesSustainabilityProfile]:
    """Get sustainability profile for a species."""
    return db.query(SpeciesSustainabilityProfile).filter(
        SpeciesSustainabilityProfile.species_name == species.lower()
    ).first()


def check_species_export_eligibility(
    db:      Session,
    species: str,
    gear_type: Optional[str] = None,
) -> dict:
    """
    Check if a species catch is eligible for export.
    Used before generating export compliance documents.
    """
    profile = get_species_sustainability(db, species)
    if not profile:
        return {
            "eligible":  None,
            "reason":    f"No sustainability profile found for {species}",
            "warnings":  ["species_not_profiled"]
        }

    warnings = []
    eligible = True

    if not profile.export_permitted:
        eligible = False
        warnings.append("export_not_permitted")

    if profile.sustainability_status == SustainabilityStatus.RED:
        eligible = False
        warnings.append("red_listed_species")

    if profile.requires_permit:
        warnings.append("permit_required_for_export")

    if gear_type and profile.prohibited_gear:
        prohibited = [g.strip() for g in profile.prohibited_gear.split(",")]
        if gear_type.lower() in prohibited:
            eligible = False
            warnings.append(f"prohibited_gear_{gear_type}")

    return {
        "species":             species,
        "eligible":            eligible,
        "sustainability":      profile.sustainability_status.value,
        "sassi_rating":        profile.sassi_rating,
        "iucn_status":         profile.iucn_status,
        "requires_permit":     profile.requires_permit,
        "minimum_size_cm":     profile.minimum_size_cm,
        "closed_season_start": profile.closed_season_start,
        "closed_season_end":   profile.closed_season_end,
        "warnings":            warnings,
        "notes":               profile.notes,
    }


# ── FISHER IMPACT PROFILE ─────────────────────────────────────────

def get_or_create_fisher_impact_profile(
    db:        Session,
    fisher_id: int,
) -> FisherImpactProfile:
    """Get existing profile or create blank one for a fisher."""
    profile = db.query(FisherImpactProfile).filter(
        FisherImpactProfile.fisher_id == fisher_id
    ).first()

    if not profile:
        profile = FisherImpactProfile(
            fisher_id       = fisher_id,
            profile_complete = False,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


def update_fisher_impact_metrics(
    db:        Session,
    fisher_id: int,
) -> FisherImpactProfile:
    """
    Recompute fisher impact metrics from transaction history.
    Call after each completed order/payout.
    """
    from app.models.payment import PaymentTransaction, PayoutStatus

    profile = get_or_create_fisher_impact_profile(db, fisher_id)

    # Count orders as fisher/supplier
    orders = db.query(Order).filter(
        Order.fisherman_id == fisher_id
    ).all()

    # Sum payouts
    order_ids = [o.id for o in orders]
    txns = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id.in_(order_ids),
        PaymentTransaction.payout_status == PayoutStatus.PAID,
    ).all() if order_ids else []

    total_earnings = sum(t.supplier_amount or 0 for t in txns)
    total_catch_kg = sum(o.quantity_kg for o in orders)

    # Primary species from catch events
    catch_events = db.query(CatchEvent).filter(
        CatchEvent.fisher_id == fisher_id
    ).all()
    species_counts = {}
    for ce in catch_events:
        species_counts[ce.species] = species_counts.get(ce.species, 0) + ce.weight_kg
    primary_species = ",".join(
        sorted(species_counts, key=species_counts.get, reverse=True)[:3]
    ) if species_counts else None

    # Last transaction
    last_order = db.query(Order).filter(
        Order.fisherman_id == fisher_id
    ).order_by(Order.created_at.desc()).first()

    profile.lifetime_catch_kg     = round(total_catch_kg, 2)
    profile.lifetime_earnings_kes = round(total_earnings, 2)
    profile.total_transactions    = len(orders)
    profile.primary_species       = primary_species
    profile.last_transaction_at   = last_order.created_at if last_order else None
    profile.last_updated_at       = datetime.now(timezone.utc)

    db.commit()
    db.refresh(profile)
    return profile


# ── ESG DASHBOARD ─────────────────────────────────────────────────

def get_esg_dashboard(db: Session) -> dict:
    """
    Platform-wide ESG impact summary.
    Used by admin, investors, ESG reporters.
    """
    now = datetime.now(timezone.utc)

    # Catch events
    total_catch_events = db.query(func.count(CatchEvent.id)).scalar()
    total_catch_kg     = db.query(func.sum(CatchEvent.weight_kg)).scalar() or 0

    # IUU risk breakdown
    iuu_low    = db.query(func.count(CatchEvent.id)).filter(
        CatchEvent.iuu_risk_level == IUURiskLevel.LOW).scalar()
    iuu_medium = db.query(func.count(CatchEvent.id)).filter(
        CatchEvent.iuu_risk_level == IUURiskLevel.MEDIUM).scalar()
    iuu_high   = db.query(func.count(CatchEvent.id)).filter(
        CatchEvent.iuu_risk_level == IUURiskLevel.HIGH).scalar()

    # Cross-border fishers
    cross_border = db.query(func.count(CatchEvent.id)).filter(
        CatchEvent.is_cross_border == True).scalar()

    # Female participation
    female_crew = db.query(func.sum(CatchEvent.female_crew_count)).scalar() or 0
    total_crew  = db.query(func.sum(CatchEvent.crew_size)).scalar() or 0

    # Species sustainability breakdown
    species_profiles = db.query(SpeciesSustainabilityProfile).all()
    sustainability_summary = {
        "green":      sum(1 for s in species_profiles if s.sustainability_status == SustainabilityStatus.GREEN),
        "orange":     sum(1 for s in species_profiles if s.sustainability_status == SustainabilityStatus.ORANGE),
        "red":        sum(1 for s in species_profiles if s.sustainability_status == SustainabilityStatus.RED),
        "unassessed": sum(1 for s in species_profiles if s.sustainability_status == SustainabilityStatus.UNASSESSED),
    }

    # Traceability chains
    total_chains   = db.query(func.count(TraceabilityChain.id)).scalar()
    export_ready   = db.query(func.count(TraceabilityChain.id)).filter(
        TraceabilityChain.export_ready == True).scalar()

    # Fisher profiles
    total_profiles = db.query(func.count(FisherImpactProfile.id)).scalar()

    return {
        "generated_at": now.isoformat(),
        "catch_data": {
            "total_catch_events":    total_catch_events,
            "total_catch_kg":        round(total_catch_kg, 2),
            "cross_border_landings": cross_border,
        },
        "iuu_risk": {
            "low":    iuu_low,
            "medium": iuu_medium,
            "high":   iuu_high,
        },
        "gender_inclusion": {
            "female_crew_total": int(female_crew),
            "total_crew":        int(total_crew),
            "female_percentage": round(female_crew / total_crew * 100, 1)
                                 if total_crew > 0 else 0,
        },
        "species_sustainability": sustainability_summary,
        "traceability": {
            "total_chains":  total_chains,
            "export_ready":  export_ready,
            "export_rate":   round(export_ready / total_chains * 100, 1)
                             if total_chains > 0 else 0,
        },
        "fisher_profiles": {
            "total_profiles": total_profiles,
        },
    }