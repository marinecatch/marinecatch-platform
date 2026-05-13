# app/services/inventory_service.py
#
# WHY THIS FILE EXISTS:
# All business logic for inventory lots lives here.
# Routes call these functions — never touch DB directly.
#
# This service supports all three modes:
# Mode 1: Fisher creates marketplace lot
# Mode 2: MarineCatch creates owned lot (procurement)
# Mode 3: Lot reserved for fulfillment contract
#
# Key operations:
# - create_lot: new inventory enters the system
# - reserve_stock: hold kg for a pending order
# - release_stock: free up reserved kg (cancelled order)
# - deduct_stock: permanently reduce after delivery
# - get_available: browse what buyers can order

from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from app.models.inventory_lot import (
    InventoryLot, OwnershipType, LotStatus,
    ProductForm, LotCondition, QualityGrade,
    FulfillmentMode, LogisticsResponsibility
)

# ── SPECIES EXPIRY MAP ────────────────────────────────────────────
# Default shelf life in days by species + condition
# Used to calculate estimated_expiry automatically
SPECIES_EXPIRY_DAYS = {
    ("tuna",    "fresh"):   3,
    ("tuna",    "frozen"):  90,
    ("octopus", "fresh"):   3,
    ("octopus", "frozen"):  60,
    ("prawns",  "fresh"):   2,
    ("prawns",  "frozen"):  90,
    ("lobster", "live"):    5,
    ("oysters", "live"):    7,
    ("crab",    "live"):    4,
    ("snapper", "fresh"):   3,
    ("snapper", "frozen"):  60,
    ("sardines","fresh"):   2,
    ("sardines","dried"):   180,
    ("kingfish","fresh"):   3,
    ("kingfish","frozen"):  60,
    ("default", "fresh"):   3,
    ("default", "frozen"):  60,
    ("default", "dried"):   180,
    ("default", "live"):    5,
}

def get_expiry_days(species: str, condition: str) -> int:
    """Look up shelf life. Falls back to default if species unknown."""
    key = (species.lower(), condition.lower())
    return SPECIES_EXPIRY_DAYS.get(key, SPECIES_EXPIRY_DAYS.get(
        ("default", condition.lower()), 3
    ))


# ── LOT NUMBER GENERATOR ──────────────────────────────────────────
def generate_lot_number(landing_site: str, ownership_type: str) -> str:
    """
    Generate human-readable lot number.
    Format: MC-LOT-YYYYMMDD-XX###
    XX = site code, ### = sequence

    Examples:
    MC-LOT-20260511-KB001 (Kibuyuni marketplace)
    MC-LOT-20260511-MC001 (MarineCatch owned)
    MC-LOT-20260511-UK001 (Ukunda)
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    site_codes = {
        "kibuyuni": "KB",
        "majoreni": "MJ",
        "shimoni":  "SH",
        "ukunda":   "UK",
        "mwambao":  "MW",
        "vanga":    "VG",
        "kinondo":  "KN",
        "malindi":  "ML",
        "lamu":     "LM",
        "mombasa":  "MB",
    }

    if ownership_type == "marinecatch_owned":
        site_code = "MC"
    else:
        site_code = site_codes.get(landing_site.lower(), "XX")

    # Simple timestamp-based sequence — good enough for MVP
    import time
    sequence = str(int(time.time()))[-3:]

    return f"MC-LOT-{today}-{site_code}{sequence}"


# ── CREATE LOT ────────────────────────────────────────────────────
def create_inventory_lot(
    db: Session,
    source_user_id: int,
    source_name: str,
    species: str,
    weight_kg: float,
    selling_price_per_kg: float,
    landing_site: str,
    ownership_type: str              = "marketplace",
    product_form: str                = "whole_ungutted",
    condition: str                   = "fresh",
    grade: str                       = "pending",
    purchase_price_per_kg: float     = None,
    min_price_per_kg: float          = None,
    cold_storage_id: int             = None,
    storage_location: str            = None,
    fulfillment_mode: str            = "self_pickup",
    logistics_responsibility: str    = "buyer",
    catch_date: str                  = None,
    landing_date: str                = None,
    vessel_reg: str                  = None,
    vessel_name: str                 = None,
    bmu_reference: str               = None,
    gear_type: str                   = None,
    batch_number: str                = None,
    notes: str                       = None,
    cold_storage_fee_per_kg_per_day: float = 0.0,
    handling_fee_kes: float          = 0.0,
    qa_fee_kes: float                = 0.0,
) -> InventoryLot:
    """
    Create a new inventory lot.

    Called when:
    - Fisher lists catch via API (Mode 1)
    - MarineCatch procures directly (Mode 2)
    - Lot reserved for contract (Mode 3)

    Auto-calculates:
    - lot_number
    - traceability_code
    - estimated_expiry
    """
    # Validate weight
    if weight_kg <= 0:
        raise HTTPException(
            status_code=400,
            detail="Weight must be greater than 0"
        )

    # Validate price
    if selling_price_per_kg <= 0:
        raise HTTPException(
            status_code=400,
            detail="Selling price must be greater than 0"
        )

    # Mode 2 validation: purchase price required
    if ownership_type == "marinecatch_owned" and not purchase_price_per_kg:
        raise HTTPException(
            status_code=400,
            detail="Purchase price required for MarineCatch-owned inventory"
        )

    now        = datetime.now(timezone.utc)
    lot_number = generate_lot_number(landing_site, ownership_type)

    # Auto-calculate expiry based on species + condition
    expiry_days     = get_expiry_days(species, condition)
    estimated_expiry = now + timedelta(days=expiry_days)

    # Traceability code — human readable + future QR/blockchain
    today_str        = now.strftime("%Y%m%d")
    traceability_code = f"MC-TRACE-{lot_number[-6:]}-{source_name.replace(' ', '').upper()[:8]}-{today_str}"

    lot = InventoryLot(
        lot_number             = lot_number,
        traceability_code      = traceability_code,
        batch_number           = batch_number,
        species                = species.lower(),
        product_form           = product_form,
        weight_kg              = weight_kg,
        available_kg           = weight_kg,
        reserved_kg            = 0.0,
        grade                  = grade,
        condition              = condition,
        source_user_id         = source_user_id,
        source_name            = source_name,
        landing_site           = landing_site.lower(),
        bmu_reference          = bmu_reference,
        catch_date             = catch_date or now.date().isoformat(),
        landing_date           = landing_date or now.date().isoformat(),
        vessel_reg             = vessel_reg,
        vessel_name            = vessel_name,
        ownership_type         = ownership_type,
        purchase_price_per_kg  = purchase_price_per_kg,
        selling_price_per_kg   = selling_price_per_kg,
        min_price_per_kg       = min_price_per_kg,
        cold_storage_id        = cold_storage_id,
        storage_location       = storage_location,
        cold_storage_fee_per_kg_per_day = cold_storage_fee_per_kg_per_day,
        handling_fee_kes       = handling_fee_kes,
        qa_fee_kes             = qa_fee_kes,
        fulfillment_mode       = fulfillment_mode,
        logistics_responsibility = logistics_responsibility,
        gear_type              = gear_type,
        iuu_risk_flag          = False,
        lot_status             = LotStatus.AVAILABLE,
        is_active              = True,
        estimated_expiry       = estimated_expiry,
        notes                  = notes,
    )

    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


# ── GET AVAILABLE LOTS ────────────────────────────────────────────
def get_available_lots(
    db: Session,
    species: str             = None,
    landing_site: str        = None,
    ownership_type: str      = None,
    condition: str           = None,
    grade: str               = None,
    min_weight_kg: float     = None,
    max_price_per_kg: float  = None,
    skip: int                = 0,
    limit: int               = 50,
) -> List[InventoryLot]:
    """
    Browse available inventory.
    Used by buyers, processors, hotels to find fish.

    Filters:
    - species: tuna, octopus, prawns...
    - landing_site: kibuyuni, shimoni...
    - ownership_type: marketplace or marinecatch_owned
    - condition: fresh, frozen, live...
    - grade: A, B, C
    - min_weight_kg: minimum available quantity
    - max_price_per_kg: buyer budget filter
    """
    query = db.query(InventoryLot).filter(
        and_(
            InventoryLot.lot_status == LotStatus.AVAILABLE,
            InventoryLot.is_active  == True,
            InventoryLot.available_kg > 0,
        )
    )

    if species:
        query = query.filter(
            InventoryLot.species == species.lower()
        )
    if landing_site:
        query = query.filter(
            InventoryLot.landing_site == landing_site.lower()
        )
    if ownership_type:
        query = query.filter(
            InventoryLot.ownership_type == ownership_type
        )
    if condition:
        query = query.filter(
            InventoryLot.condition == condition.lower()
        )
    if grade:
        query = query.filter(InventoryLot.grade == grade)
    if min_weight_kg:
        query = query.filter(
            InventoryLot.available_kg >= min_weight_kg
        )
    if max_price_per_kg:
        query = query.filter(
            InventoryLot.selling_price_per_kg <= max_price_per_kg
        )

    return query.order_by(
        InventoryLot.created_at.desc()
    ).offset(skip).limit(limit).all()


# ── GET SINGLE LOT ────────────────────────────────────────────────
def get_lot_by_id(db: Session, lot_id: int) -> Optional[InventoryLot]:
    return db.query(InventoryLot).filter(
        InventoryLot.id == lot_id
    ).first()

def get_lot_by_number(db: Session, lot_number: str) -> Optional[InventoryLot]:
    return db.query(InventoryLot).filter(
        InventoryLot.lot_number == lot_number
    ).first()


# ── RESERVE STOCK ─────────────────────────────────────────────────
def reserve_stock(
    db: Session,
    lot_id: int,
    quantity_kg: float
) -> InventoryLot:
    """
    Reserve kg for a pending order.
    Reduces available_kg, increases reserved_kg.
    Called when buyer places order (before payment).

    available_kg decreases → prevents double-selling
    reserved_kg increases → tracks what's held
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    if lot.lot_status != LotStatus.AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Lot is not available. Current status: {lot.lot_status}"
        )

    if quantity_kg > lot.available_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {lot.available_kg}kg, Requested: {quantity_kg}kg"
        )

    lot.available_kg -= quantity_kg
    lot.reserved_kg  += quantity_kg

    # Update status
    if lot.available_kg <= 0:
        lot.lot_status = LotStatus.RESERVED
    else:
        lot.lot_status = LotStatus.PARTIALLY_SOLD

   # Don't commit here — caller owns the transaction
    return lot
# ── RELEASE STOCK ─────────────────────────────────────────────────
def release_stock(
    db: Session,
    lot_id: int,
    quantity_kg: float
) -> InventoryLot:
    """
    Release reserved stock back to available.
    Called when order is cancelled before delivery.
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    lot.reserved_kg  = max(0, lot.reserved_kg - quantity_kg)
    lot.available_kg += quantity_kg

    # Restore to available if stock freed up
    if lot.available_kg > 0:
        lot.lot_status = LotStatus.AVAILABLE

    # Don't commit here — caller owns the transaction
    return lot


# ── DEDUCT STOCK (PERMANENT) ──────────────────────────────────────
def deduct_stock(
    db: Session,
    lot_id: int,
    quantity_kg: float
) -> InventoryLot:
    """
    Permanently deduct stock after confirmed delivery.
    Reduces reserved_kg (not available_kg — already reduced on reserve).
    Marks lot as SOLD if nothing left.
    """
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    lot.reserved_kg = max(0, lot.reserved_kg - quantity_kg)

    # Mark as sold if both available and reserved are zero
    if lot.available_kg <= 0 and lot.reserved_kg <= 0:
        lot.lot_status = LotStatus.SOLD
        lot.is_active  = False

    db.commit()
    db.refresh(lot)
    return lot


# ── GET LOTS BY FISHER ────────────────────────────────────────────
def get_lots_by_fisher(
    db: Session,
    fisher_id: int,
    include_sold: bool = False
) -> List[InventoryLot]:
    """Get all inventory lots for a specific fisher."""
    query = db.query(InventoryLot).filter(
        InventoryLot.source_user_id == fisher_id
    )
    if not include_sold:
        query = query.filter(InventoryLot.is_active == True)

    return query.order_by(InventoryLot.created_at.desc()).all()


# ── CALCULATE ORDER VALUE ─────────────────────────────────────────
def calculate_order_value(
    lot: InventoryLot,
    quantity_kg: float
) -> dict:
    """
    Calculate full cost breakdown for an order.
    This is the revenue stack:
      fish value + platform commission + storage fee + handling + QA + delivery
    """
    # Base fish value
    fish_value_kes = round(quantity_kg * lot.selling_price_per_kg, 2)

    # Platform commission (tiered)
    if fish_value_kes < 5000:
        commission_rate = 0.035
    elif fish_value_kes < 50000:
        commission_rate = 0.025
    else:
        commission_rate = 0.015

    platform_commission_kes = round(fish_value_kes * commission_rate, 2)

    # Storage fee (per kg, prorated — simplified for MVP)
    cold_storage_fee_kes = round(
        quantity_kg * lot.cold_storage_fee_per_kg_per_day, 2
    )

    # Handling and QA fees (fixed per lot, prorated by quantity)
    lot_proportion = quantity_kg / lot.weight_kg if lot.weight_kg > 0 else 1
    handling_fee_kes = round(lot.handling_fee_kes * lot_proportion, 2)
    qa_fee_kes       = round(lot.qa_fee_kes * lot_proportion, 2)

    # Total buyer pays
    total_buyer_pays_kes = round(
        fish_value_kes
        + platform_commission_kes
        + cold_storage_fee_kes
        + handling_fee_kes
        + qa_fee_kes,
        2
    )

    # Net to seller (fish value minus commission)
    net_to_seller_kes = round(
        fish_value_kes - platform_commission_kes, 2
    )

    # MarineCatch margin (Mode 2 only)
    marinecatch_margin_kes = None
    if lot.ownership_type == "marinecatch_owned" and lot.purchase_price_per_kg:
        procurement_cost = round(quantity_kg * lot.purchase_price_per_kg, 2)
        marinecatch_margin_kes = round(
            fish_value_kes - procurement_cost, 2
        )

    return {
        "quantity_kg":            quantity_kg,
        "price_per_kg":           lot.selling_price_per_kg,
        "fish_value_kes":         fish_value_kes,
        "commission_rate":        f"{commission_rate * 100}%",
        "platform_commission_kes": platform_commission_kes,
        "cold_storage_fee_kes":   cold_storage_fee_kes,
        "handling_fee_kes":       handling_fee_kes,
        "qa_fee_kes":             qa_fee_kes,
        "total_buyer_pays_kes":   total_buyer_pays_kes,
        "net_to_seller_kes":      net_to_seller_kes,
        "marinecatch_margin_kes": marinecatch_margin_kes,
        "ownership_type":         lot.ownership_type,
    }