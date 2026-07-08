# app/api/v1/routes/inventory.py
#
# WHY THIS FILE EXISTS:
# Handles all HTTP requests for inventory lots.
# Replaces the old fish.py marketplace logic with
# a proper inventory system supporting all 3 modes.
#
# Public endpoints (no login):
#   GET /inventory          → browse available lots
#   GET /inventory/{id}     → single lot details
#
# Protected endpoints (login required):
#   POST /inventory         → fisher/supplier creates lot
#   GET  /inventory/my-lots → fisher sees their own lots
#   POST /inventory/{id}/reserve → reserve stock for order

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.services.inventory_service import (
    create_inventory_lot,
    get_available_lots,
    get_lot_by_id,
    get_lots_by_fisher,
    calculate_order_value,
    reserve_stock,
    release_stock,
)
from app.api.v1.routes.users import get_current_user
from app.services.fee_service import calculate_full_fee_breakdown
from app.models.inventory_lot import InventoryLot
from app.models.quality_inspection import QualityInspection

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# ── PUBLIC — browse available lots ───────────────────────────────
@router.get("/")
def browse_inventory(
    species:          Optional[str]   = Query(None),
    landing_site:     Optional[str]   = Query(None),
    condition:        Optional[str]   = Query(None),
    grade:            Optional[str]   = Query(None),
    min_weight_kg:    Optional[float] = Query(None),
    max_price_per_kg: Optional[float] = Query(None),
    page:             int             = Query(1, ge=1),
    page_size:        int             = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Browse all available seafood inventory.
    Public — no login required.

    Examples:
    /api/v1/inventory?species=tuna
    /api/v1/inventory?landing_site=kibuyuni
    /api/v1/inventory?condition=fresh&max_price_per_kg=800
    /api/v1/inventory?species=prawns&grade=A
    """
    skip = (page - 1) * page_size
    lots = get_available_lots(
        db,
        species=          species,
        landing_site=     landing_site,
        condition=        condition,
        grade=            grade,
        min_weight_kg=    min_weight_kg,
        max_price_per_kg= max_price_per_kg,
        skip=             skip,
        limit=            page_size,
    )

    return {
        "page":      page,
        "page_size": page_size,
        "count":     len(lots),
        "lots": [
            {
                "id":                   lot.id,
                "lot_number":           lot.lot_number,
                "traceability_code":    lot.traceability_code,
                "species":              lot.species,
                "product_form":         lot.product_form,
                "weight_kg":            lot.weight_kg,
                "available_kg":         lot.available_kg,
                "selling_price_per_kg": lot.selling_price_per_kg,
                "total_value_kes":      round(
                    lot.available_kg * lot.selling_price_per_kg, 2
                ),
                "grade":                lot.grade,
                "condition":            lot.condition,
                "landing_site":         lot.landing_site,
                "source_name":          lot.source_name,
                "catch_date":           lot.catch_date,
                "ownership_type":       lot.ownership_type,
                "fulfillment_mode":     lot.fulfillment_mode,
                "estimated_expiry":     lot.estimated_expiry,
                "notes":                lot.notes,
            }
            for lot in lots
        ]
    }

# ── PUBLIC — traceability lookup by code (for QR codes / trace page) ────
@router.get("/trace/{traceability_code}")
def get_trace_by_code(traceability_code: str, db: Session = Depends(get_db)):
    """
    Public traceability lookup — no login required.
    Powers the QR-code trace page so buyers, partners, or auditors
    can verify a lot's full chain from catch to listing.
    """
    lot = db.query(InventoryLot).filter(
        InventoryLot.traceability_code == traceability_code
    ).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Traceability record not found")

    inspection = db.query(QualityInspection).filter(
        QualityInspection.lot_id == lot.id
    ).first()

    return {
        "lot_number":            lot.lot_number,
        "traceability_code":     lot.traceability_code,
        "species":                lot.species,
        "product_form":           lot.product_form,
        "grade":                  lot.grade,
        "condition":              lot.condition,
        "weight_kg":              lot.weight_kg,
        "source_name":            lot.source_name,
        "landing_site":           lot.landing_site,
        "catch_date":             lot.catch_date,
        "landing_date":           lot.landing_date,
        "vessel_name":            lot.vessel_name,
        "vessel_reg":             lot.vessel_reg,
        "bmu_reference":          lot.bmu_reference,
        "gear_type":              lot.gear_type,
        "ownership_type":         lot.ownership_type,
        "lot_status":             lot.lot_status,
        "iuu_risk_flag":          lot.iuu_risk_flag,
        "sustainability_notes":   lot.sustainability_notes,
        "created_at":             lot.created_at,
        "inspection": {
            "status":         inspection.status,
            "grade":          inspection.grade,
            "inspector_name": inspection.inspector_name,
            "temperature_c":  inspection.temperature_c,
            "inspected_at":   inspection.inspected_at,
            "disposition":    inspection.disposition,
        } if inspection else None,
    }

# ── PUBLIC — single lot detail ────────────────────────────────────
@router.get("/{lot_id}")
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    """
    Get full details of one inventory lot.
    Includes traceability, storage, and fee breakdown.
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    return {
        "id":                          lot.id,
        "lot_number":                  lot.lot_number,
        "traceability_code":           lot.traceability_code,
        "batch_number":                lot.batch_number,
        "species":                     lot.species,
        "product_form":                lot.product_form,
        "weight_kg":                   lot.weight_kg,
        "available_kg":                lot.available_kg,
        "reserved_kg":                 lot.reserved_kg,
        "grade":                       lot.grade,
        "condition":                   lot.condition,
        "source_name":                 lot.source_name,
        "landing_site":                lot.landing_site,
        "catch_date":                  lot.catch_date,
        "landing_date":                lot.landing_date,
        "vessel_reg":                  lot.vessel_reg,
        "bmu_reference":               lot.bmu_reference,
        "gear_type":                   lot.gear_type,
        "ownership_type":              lot.ownership_type,
        "selling_price_per_kg":        lot.selling_price_per_kg,
        "cold_storage_fee_per_kg_per_day": lot.cold_storage_fee_per_kg_per_day,
        "handling_fee_kes":            lot.handling_fee_kes,
        "qa_fee_kes":                  lot.qa_fee_kes,
        "fulfillment_mode":            lot.fulfillment_mode,
        "logistics_responsibility":    lot.logistics_responsibility,
        "lot_status":                  lot.lot_status,
        "estimated_expiry":            lot.estimated_expiry,
        "iuu_risk_flag":               lot.iuu_risk_flag,
        "notes":                       lot.notes,
        "created_at":                  lot.created_at,
    }

# ── PROTECTED — fisher creates lot ───────────────────────────────
@router.post("/", status_code=201)
def create_lot(
    species:              str,
    weight_kg:            float,
    selling_price_per_kg: float,
    landing_site:         str,
    condition:            str   = "fresh",
    product_form:         str   = "whole_ungutted",
    vessel_reg:           Optional[str]   = None,
    bmu_reference:        Optional[str]   = None,
    gear_type:            Optional[str]   = None,
    notes:                Optional[str]   = None,
    cold_storage_id:      Optional[int]   = None,
    storage_location:     Optional[str]   = None,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    Fisher or supplier creates a new inventory lot.
    Requires login — fisher or supplier role only.

    Example:
    Abdalla Masudi lists 40kg fresh octopus from Kibuyuni.
    System auto-generates lot number and traceability code.
    """
    if current_user.role not in ["fisher", "supplier", "admin"]:
        raise HTTPException(
            status_code=403,
            detail=f"Only fishers and suppliers can create listings. Your role: {current_user.role}"
        )

    lot = create_inventory_lot(
        db=                   db,
        source_user_id=       current_user.id,
        source_name=          current_user.name,
        species=              species,
        weight_kg=            weight_kg,
        selling_price_per_kg= selling_price_per_kg,
        landing_site=         landing_site,
        ownership_type=       "marketplace",
        product_form=         product_form,
        condition=            condition,
        vessel_reg=           vessel_reg,
        bmu_reference=        bmu_reference,
        gear_type=            gear_type,
        cold_storage_id=      cold_storage_id,
        storage_location=     storage_location,
        notes=                notes,
    )

    return {
        "success":          True,
        "lot_number":       lot.lot_number,
        "traceability_code":lot.traceability_code,
        "species":          lot.species,
        "weight_kg":        lot.weight_kg,
        "selling_price_per_kg": lot.selling_price_per_kg,
        "total_value_kes":  round(lot.weight_kg * lot.selling_price_per_kg, 2),
        "estimated_expiry": lot.estimated_expiry,
        "lot_status":       lot.lot_status,
        "message":          f"Lot {lot.lot_number} created successfully"
    }

# ── PROTECTED — fisher sees their lots ───────────────────────────
@router.get("/my-lots/list")
def get_my_lots(
    include_sold: bool   = Query(False),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    Fisher or supplier sees all their inventory lots.
    Shows earnings summary.
    """
    lots = get_lots_by_fisher(db, current_user.id, include_sold)

    total_available_kg    = sum(l.available_kg for l in lots)
    total_value_available = sum(
        l.available_kg * l.selling_price_per_kg for l in lots
    )

    return {
        "fisher":               current_user.name,
        "total_lots":           len(lots),
        "total_available_kg":   round(total_available_kg, 2),
        "total_value_kes":      round(total_value_available, 2),
        "lots": [
            {
                "id":               l.id,
                "lot_number":       l.lot_number,
                "species":          l.species,
                "weight_kg":        l.weight_kg,
                "available_kg":     l.available_kg,
                "reserved_kg":      l.reserved_kg,
                "selling_price_per_kg": l.selling_price_per_kg,
                "lot_status":       l.lot_status,
                "catch_date":       l.catch_date,
                "estimated_expiry": l.estimated_expiry,
            }
            for l in lots
        ]
    }

# ── PROTECTED — calculate order value before placing ─────────────
@router.get("/{lot_id}/quote")
def get_quote(
    lot_id:      int,
    quantity_kg: float = Query(..., gt=0),
    db: Session  = Depends(get_db)
):
    """
    Get full price breakdown before placing order.
    Shows fish value + all fees + net to seller.

    Example:
    Neptune Hotels wants to know total cost for 30kg tuna.
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    if quantity_kg > lot.available_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Only {lot.available_kg}kg available"
        )

    return calculate_order_value(lot, quantity_kg)
# ── INTERNAL — reserve stock for an order ─────────────────────────
@router.post("/{lot_id}/reserve")
def reserve_lot(
    lot_id:      int,
    quantity_kg: float = Query(..., gt=0),
    db: Session  = Depends(get_db)
):
    """
    Reserve kg against a lot when an order is placed.
    Reduces available_kg immediately — prevents double-selling.
    Called by order service, not directly by buyers.
    """
    lot = reserve_stock(db, lot_id, quantity_kg)
    return {
        "success":      True,
        "lot_number":   lot.lot_number,
        "species":      lot.species,
        "reserved_kg":  lot.reserved_kg,
        "available_kg": lot.available_kg,
        "lot_status":   lot.lot_status,
        "message":      f"{quantity_kg}kg reserved from {lot.lot_number}"
    }


# ── INTERNAL — release stock if order cancelled ───────────────────
@router.post("/{lot_id}/release")
def release_lot(
    lot_id:      int,
    quantity_kg: float = Query(..., gt=0),
    db: Session  = Depends(get_db)
):
    """
    Release reserved stock back to available.
    Called when an order is cancelled before delivery.
    Real world: buyer changed mind, payment failed, order expired.
    """
    lot = release_stock(db, lot_id, quantity_kg)
    return {
        "success":      True,
        "lot_number":   lot.lot_number,
        "available_kg": lot.available_kg,
        "reserved_kg":  lot.reserved_kg,
        "lot_status":   lot.lot_status,
        "message":      f"{quantity_kg}kg released back to available"
    }
# ── FULL FEE BREAKDOWN ────────────────────────────────────────────

@router.get("/{lot_id}/fees")
def get_fee_breakdown(
    lot_id:               int,
    quantity_kg:          float = Query(..., gt=0),
    storage_days:         int   = Query(1, ge=0),
    delivery_distance_km: float = Query(None),
    is_export_grade:      bool  = Query(False),
    db: Session = Depends(get_db),
):
    """
    Full fee breakdown before placing an order.
    Shows every cost component separately.

    Used by:
    - Buyers to see total cost before confirming
    - Hotels to compare delivery options
    - Processors to calculate landed cost
    - Admin to verify fee accuracy
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    if quantity_kg > lot.available_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Only {lot.available_kg}kg available"
        )

    return calculate_full_fee_breakdown(
        lot=                  lot,
        quantity_kg=          quantity_kg,
        storage_days=         storage_days,
        delivery_distance_km= delivery_distance_km,
        is_export_grade=      is_export_grade,
    )
    from pydantic import BaseModel

class LotUpdateRequest(BaseModel):
    selling_price_per_kg: Optional[float] = None
    min_price_per_kg:     Optional[float] = None
    lot_status:           Optional[str]   = None
    visibility:           Optional[str]   = None
    notes:                Optional[str]   = None
    weight_kg:            Optional[float] = None

# ── PROTECTED — update lot (admin only) ──────────────────────────
@router.patch("/{lot_id}")
def update_lot(
    lot_id:  int,
    payload: LotUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Update inventory lot — used by Set Price in admin panel."""
    if str(current_user.role).lower() not in ["admin", "userrole.admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    if payload.selling_price_per_kg is not None and payload.selling_price_per_kg > 0:
        lot.selling_price_per_kg = payload.selling_price_per_kg
    if payload.min_price_per_kg is not None:
        lot.min_price_per_kg = payload.min_price_per_kg
    if payload.lot_status is not None:
        lot.lot_status = payload.lot_status
    if payload.visibility is not None:
        lot.visibility = payload.visibility
    if payload.notes is not None:
        lot.notes = payload.notes
    if payload.weight_kg is not None and payload.weight_kg > 0:
        lot.weight_kg    = payload.weight_kg
        lot.available_kg = payload.weight_kg

    db.commit()
    db.refresh(lot)

    return {
        "success":              True,
        "lot_number":           lot.lot_number,
        "selling_price_per_kg": lot.selling_price_per_kg,
        "weight_kg":            lot.weight_kg,
        "lot_status":           lot.lot_status,
        "message":              f"Lot {lot.lot_number} updated successfully"
    }