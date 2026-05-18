# app/services/lpo_service.py
#
# WHY THIS FILE EXISTS:
# LPO (Local Purchase Order) flow for institutional buyers.
# Many African seafood transactions are NOT "click buy now."
# They are WhatsApp requests, procurement calls, PDF LPOs.
#
# This service bridges:
# informal procurement ↔ structured digital commerce
#
# Flow:
# 1. Neptune Hotels sends LPO via WhatsApp/email
# 2. Admin receives it and logs it here
# 3. System creates order with LPO reference
# 4. Admin assigns inventory lots to fulfill it
# 5. Order moves through normal lifecycle
# 6. Invoice generated on completion

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional

from app.models.order import Order, OrderStatus, OrderType
from app.models.user import User
from app.models.inventory_lot import InventoryLot, LotStatus
from app.services.inventory_service import reserve_stock
from app.services.fee_service import calculate_full_fee_breakdown


# ── CREATE LPO ORDER ──────────────────────────────────────────────

def create_lpo_order(
    db:                      Session,
    buyer_id:                int,
    lot_id:                  int,
    quantity_kg:             float,
    lpo_reference:           str,
    procurement_officer:     Optional[str]     = None,
    expected_fulfillment_date: Optional[str]   = None,
    payment_terms_days:      int               = 7,
    delivery_address:        Optional[str]     = None,
    delivery_distance_km:    Optional[float]   = None,
    notes:                   Optional[str]     = None,
    created_by:              str               = "admin",
) -> Order:
    """
    Create an order from an institutional LPO.
    Called by admin when LPO is received via WhatsApp/email/phone.

    Key differences from marketplace order:
    - order_source = "lpo"
    - lpo_reference stored for document tracking
    - payment_terms_days set from buyer's credit terms
    - No immediate STK Push — invoice issued instead
    - reserved_until = None (institutional buyers don't auto-expire)

    Real example:
    Neptune Hotels sends LPO-2026-0142 for 50kg tuna, Net 7 terms.
    Admin logs it. System reserves stock, creates order, issues invoice.
    """

    # Validate buyer exists
    buyer = db.query(User).filter(User.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    # Validate lot exists and is available
    lot = db.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Inventory lot not found")

    if lot.lot_status not in [LotStatus.AVAILABLE, LotStatus.PARTIALLY_SOLD]:
        raise HTTPException(
            status_code=400,
            detail=f"Lot is not available. Status: {lot.lot_status.value}"
        )

    if quantity_kg > lot.available_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {lot.available_kg}kg, Requested: {quantity_kg}kg"
        )

    # Validate LPO reference not already used
    existing = db.query(Order).filter(
        Order.lpo_reference == lpo_reference
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"LPO reference {lpo_reference} already exists as order {existing.id}"
        )

    # Calculate fees
    fees = calculate_full_fee_breakdown(
        lot=                  lot,
        quantity_kg=          quantity_kg,
        delivery_distance_km= delivery_distance_km,
    )

    # Reserve stock
    reserve_stock(db, lot_id, quantity_kg)

    # Build notes
    full_notes = []
    if procurement_officer:
        full_notes.append(f"Procurement officer: {procurement_officer}")
    if expected_fulfillment_date:
        full_notes.append(f"Expected fulfillment: {expected_fulfillment_date}")
    if notes:
        full_notes.append(notes)
    full_notes.append(f"LPO logged by: {created_by}")

    # Create order
    order = Order(
        buyer_id          = buyer_id,
        lot_id            = lot_id,
        fisherman_id      = lot.source_user_id,
        order_type        = OrderType.FULFILLMENT,
        order_source      = "lpo",
        lpo_reference     = lpo_reference,
        species           = lot.species,
        landing_site      = lot.landing_site,
        quantity_kg       = quantity_kg,
        price_per_kg      = lot.selling_price_per_kg,
        total_kes         = fees["totals"]["total_buyer_pays_kes"],
        platform_fee_kes  = fees["fees"]["commission"]["commission_kes"],
        net_to_fisher_kes = fees["totals"]["net_to_seller_kes"],
        commission_rate   = fees["fees"]["commission"]["commission_rate"],
        delivery_address  = delivery_address,
        delivery_distance_km = delivery_distance_km,
        payment_terms_days   = payment_terms_days,
        status            = OrderStatus.CONFIRMED,
        reserved_until    = None,
        notes             = " | ".join(full_notes) if full_notes else None,
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# ── GET LPO ORDER ─────────────────────────────────────────────────

def get_order_by_lpo(db: Session, lpo_reference: str) -> Optional[Order]:
    """Find an order by its LPO reference number."""
    return db.query(Order).filter(
        Order.lpo_reference == lpo_reference
    ).first()


# ── LIST LPO ORDERS ───────────────────────────────────────────────

def get_all_lpo_orders(
    db:    Session,
    limit: int = 50,
) -> list:
    """All orders that came from LPOs."""
    orders = db.query(Order).filter(
        Order.order_source == "lpo"
    ).order_by(Order.created_at.desc()).limit(limit).all()

    results = []
    for order in orders:
        buyer = db.query(User).filter(User.id == order.buyer_id).first()
        results.append({
            "order_id":          order.id,
            "lpo_reference":     order.lpo_reference,
            "buyer_name":        buyer.name if buyer else None,
            "species":           order.species,
            "quantity_kg":       order.quantity_kg,
            "total_kes":         order.total_kes,
            "payment_terms_days": order.payment_terms_days,
            "status":            order.status.value,
            "created_at":        order.created_at,
            "notes":             order.notes,
        })

    return results