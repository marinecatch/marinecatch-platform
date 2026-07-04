# app/api/v1/routes/compliance.py
#
# Compliance profile and member ID management.
# Quality inspection workflow.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.compliance_profile import ComplianceProfile
from app.models.quality_inspection import QualityInspection
from app.models.inventory_lot import InventoryLot, LotStatus
from app.models.user import User
from app.services.member_id_service import (
    create_compliance_profile,
    upgrade_compliance_level,
    verify_national_id,
    verify_bmu,
    verify_kra,
    get_profile,
    get_profile_by_member_id,
    update_trust_score,
    seed_compliance_profiles_for_existing_users,
)

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class NationalIDVerify(BaseModel):
    user_id:     int
    national_id: str

class BMUVerify(BaseModel):
    user_id:               int
    bmu_membership_number: str
    bmu_name:              str
    fisher_cluster_id:     Optional[int] = None
    default_landing_site:  Optional[str] = None

class KRAVerify(BaseModel):
    user_id: int
    kra_pin: str

class InspectionCreate(BaseModel):
    lot_id:            int
    grade:             str  # A, B, C, R
    disposition:       str
    temperature_c:     Optional[float] = None
    temperature_ok:    Optional[bool]  = None
    smell_ok:          Optional[bool]  = None
    texture_ok:        Optional[bool]  = None
    appearance_ok:     Optional[bool]  = None
    ice_ratio_ok:      Optional[bool]  = None
    gills_ok:          Optional[bool]  = None
    eyes_ok:           Optional[bool]  = None
    declared_weight_kg: Optional[float] = None
    verified_weight_kg: Optional[float] = None
    rejection_reason:  Optional[str]   = None
    conditions:        Optional[str]   = None
    notes:             Optional[str]   = None


# ── COMPLIANCE PROFILES ───────────────────────────────────────────

@router.post("/seed-existing-users")
def seed_profiles(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """One-time: create compliance profiles for all existing users."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    count = seed_compliance_profiles_for_existing_users(db)
    return {"success": True, "profiles_created": count}


@router.get("/profiles")
def list_profiles(
    compliance_level: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """List all compliance profiles."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(ComplianceProfile)
    if compliance_level is not None:
        query = query.filter(
            ComplianceProfile.compliance_level == compliance_level
        )

    profiles = query.order_by(ComplianceProfile.id.asc()).all()
    result   = []

    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "id":                p.id,
            "user_id":           p.user_id,
            "user_name":         user.name if user else "—",
            "user_phone":        user.phone if user else "—",
            "user_role":         user.role if user else "—",
            "member_id":         p.member_id,
            "compliance_level":  p.compliance_level,
            "phone_verified":    p.phone_verified,
            "national_id_verified": p.national_id_verified,
            "bmu_verified":      p.bmu_verified,
            "bmu_name":          p.bmu_name,
            "kra_verified":      p.kra_verified,
            "trust_score":       p.trust_score,
            "buyer_tier":        p.buyer_tier,
            "total_transactions": p.total_transactions,
            "total_value_kes":   p.total_value_kes,
            "created_at":        p.created_at,
        })

    return {"total": len(result), "profiles": result}


@router.get("/profiles/{user_id}")
def get_user_profile(
    user_id:     int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Get compliance profile for a specific user."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    profile = get_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    user = db.query(User).filter(User.id == user_id).first()
    return {
        "member_id":           profile.member_id,
        "compliance_level":    profile.compliance_level,
        "user_name":           user.name if user else "—",
        "phone_verified":      profile.phone_verified,
        "national_id_verified": profile.national_id_verified,
        "bmu_verified":        profile.bmu_verified,
        "bmu_name":            profile.bmu_name,
        "bmu_membership_number": profile.bmu_membership_number,
        "kra_verified":        profile.kra_verified,
        "kra_pin":             profile.kra_pin if current_user.role == "admin" else "***",
        "trust_score":         profile.trust_score,
        "buyer_tier":          profile.buyer_tier,
        "total_transactions":  profile.total_transactions,
        "total_volume_kg":     profile.total_volume_kg,
        "total_value_kes":     profile.total_value_kes,
        "fisher_cluster_id":   profile.fisher_cluster_id,
        "default_landing_site": profile.default_landing_site,
        "verified_by":         profile.verified_by,
        "first_verified_at":   profile.first_verified_at,
    }


@router.post("/verify/national-id")
def verify_id(
    payload:     NationalIDVerify,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Verify a user's national ID."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    profile = verify_national_id(
        db, payload.user_id, payload.national_id, current_user.name
    )
    return {"success": True, "member_id": profile.member_id,
            "compliance_level": profile.compliance_level}


@router.post("/verify/bmu")
def verify_bmu_endpoint(
    payload:     BMUVerify,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Verify BMU membership — upgrades to level 2."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    profile = verify_bmu(
        db,
        payload.user_id,
        payload.bmu_membership_number,
        payload.bmu_name,
        payload.fisher_cluster_id,
        payload.default_landing_site,
        current_user.name,
    )
    return {"success": True, "member_id": profile.member_id,
            "compliance_level": profile.compliance_level}


@router.post("/verify/kra")
def verify_kra_endpoint(
    payload:     KRAVerify,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Verify KRA PIN — upgrades to level 3."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    profile = verify_kra(
        db, payload.user_id, payload.kra_pin, current_user.name
    )
    return {"success": True, "member_id": profile.member_id,
            "compliance_level": profile.compliance_level}


@router.post("/trust-score/{user_id}/recalculate")
def recalculate_trust(
    user_id:     int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Recalculate trust score for a user."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    profile = update_trust_score(db, user_id)
    return {"success": True, "trust_score": profile.trust_score}


# ── QUALITY INSPECTIONS ───────────────────────────────────────────

@router.post("/inspections", status_code=201)
def create_inspection(
    payload:     InspectionCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    Record a quality inspection for an inventory lot.
    Passing inspection makes the lot available for marketplace.
    Failing inspection changes disposition.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    lot = db.query(InventoryLot).filter(
        InventoryLot.id == payload.lot_id
    ).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Check if inspection already exists
    existing = db.query(QualityInspection).filter(
        QualityInspection.lot_id == payload.lot_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Inspection already exists for lot {lot.lot_number}"
        )

    # Determine status from grade
    grade_map = {"A": "passed", "B": "passed", "C": "conditional", "R": "failed"}
    status    = grade_map.get(payload.grade.upper(), "failed")

    # Calculate weight variance
    weight_variance = None
    if payload.declared_weight_kg and payload.verified_weight_kg:
        weight_variance = abs(
            payload.verified_weight_kg - payload.declared_weight_kg
        )

    inspection = QualityInspection(
        lot_id             = payload.lot_id,
        inspector_id       = current_user.id,
        inspector_name     = current_user.name,
        status             = status,
        grade              = payload.grade.upper(),
        disposition        = payload.disposition,
        temperature_c      = payload.temperature_c,
        temperature_ok     = payload.temperature_ok,
        smell_ok           = payload.smell_ok,
        texture_ok         = payload.texture_ok,
        appearance_ok      = payload.appearance_ok,
        ice_ratio_ok       = payload.ice_ratio_ok,
        gills_ok           = payload.gills_ok,
        eyes_ok            = payload.eyes_ok,
        declared_weight_kg = payload.declared_weight_kg,
        verified_weight_kg = payload.verified_weight_kg,
        weight_variance_kg = weight_variance,
        rejection_reason   = payload.rejection_reason,
        conditions         = payload.conditions,
        notes              = payload.notes,
        inspected_at       = datetime.now(),
    )
    db.add(inspection)

    # Update lot status based on inspection result
    if status == "passed":
        lot.lot_status = LotStatus.AVAILABLE
    elif status == "failed":
        lot.lot_status = LotStatus.EXPIRED  # Reuse as rejected status for now
    # conditional stays available but with notes

    db.commit()
    db.refresh(inspection)

    return {
        "success":      True,
        "lot_number":   lot.lot_number,
        "grade":        inspection.grade,
        "status":       inspection.status,
        "disposition":  inspection.disposition,
        "lot_status":   lot.lot_status,
    }


@router.get("/inspections")
def list_inspections(
    status:      Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """List all quality inspections."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(QualityInspection)
    if status:
        query = query.filter(QualityInspection.status == status)

    inspections = query.order_by(
        QualityInspection.inspected_at.desc()
    ).all()

    result = []
    for i in inspections:
        lot = db.query(InventoryLot).filter(
            InventoryLot.id == i.lot_id
        ).first()
        result.append({
            "id":              i.id,
            "lot_number":      lot.lot_number if lot else "—",
            "species":         lot.species if lot else "—",
            "weight_kg":       lot.weight_kg if lot else 0,
            "grade":           i.grade,
            "status":          i.status,
            "disposition":     i.disposition,
            "temperature_c":   i.temperature_c,
            "rejection_reason": i.rejection_reason,
            "inspector_name":  i.inspector_name,
            "inspected_at":    i.inspected_at,
        })

    return {"total": len(result), "inspections": result}


@router.get("/inspections/pending")
def pending_inspections(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Get all lots awaiting inspection."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Lots with no inspection record
    inspected_lot_ids = db.query(QualityInspection.lot_id).all()
    inspected_ids     = [i[0] for i in inspected_lot_ids]

    pending_lots = db.query(InventoryLot).filter(
        ~InventoryLot.id.in_(inspected_ids) if inspected_ids else True,
        InventoryLot.available_kg > 0,
    ).order_by(InventoryLot.created_at.desc()).all()

    result = []
    for lot in pending_lots:
        source = db.query(User).filter(
            User.id == lot.source_user_id
        ).first() if lot.source_user_id else None
        result.append({
            "lot_id":      lot.id,
            "lot_number":  lot.lot_number,
            "species":     lot.species,
            "weight_kg":   lot.weight_kg,
            "landing_site": lot.landing_site,
            "source_name": source.name if source else lot.source_name,
            "catch_date":  lot.catch_date,
            "created_at":  lot.created_at,
        })

    return {"total": len(result), "pending": result}