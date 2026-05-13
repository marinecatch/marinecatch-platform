# app/services/order_service.py
#
# WHY THIS FILE EXISTS:
# All business logic for placing and managing orders.
# Routes call these functions — no DB access in routes.
#
# This service connects three things:
# 1. InventoryLot — the fish being sold
# 2. Order — the transaction record
# 3. User — the buyer
#
# Supports all three business modes:
# Mode 1: Marketplace order (fisher lists, buyer orders)
# Mode 2: MarineCatch-owned inventory order
# Mode 3: Fulfillment/contract order (Phase 3)
#
# Payment integration (M-Pesa) comes in Phase 2.
# For now, orders start as PENDING_PAYMENT.
# Admin manually confirms payment until M-Pesa is live.

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List

from app.models.order import Order, OrderStatus, OrderType
from app.models.inventory_lot import InventoryLot, LotStatus
from app.services.inventory_service import (
    get_lot_by_id,
    reserve_stock,
    release_stock,
    calculate_order_value,
)


# ── PLACE ORDER ───────────────────────────────────────────────────
def place_order(
    db:               Session,
    buyer_id:         int,
    lot_id:           int,
    quantity_kg:      float,
    delivery_address: Optional[str] = None,
    notes:            Optional[str] = None,
) -> Order:
    """
    Core order placement function.

    What happens step by step:
    1. Fetch the lot — confirm it exists
    2. Confirm lot is available and has enough stock
    3. Reserve the stock immediately
    4. Calculate full price breakdown
    5. Create the order record
    6. Return the order

    If any step fails, nothing is saved.
    Stock is never reserved without an order record.

    Real world:
    Neptune Hotels wants 20kg tuna from Bakari's lot.
    System holds that 20kg, calculates total cost,
    creates the order, waits for payment.
    """

    # Step 1 — fetch the lot
    lot = get_lot_by_id(db, lot_id)
    if not lot:
        raise HTTPException(
            status_code=404,
            detail=f"Inventory lot {lot_id} not found"
        )

    # Step 2 — check lot is active
    if not lot.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Lot {lot.lot_number} is no longer active"
        )

    # Step 3 — check enough stock available
    if quantity_kg > lot.available_kg:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock. "
                f"Requested: {quantity_kg}kg, "
                f"Available: {lot.available_kg}kg"
            )
        )

    # Step 4 — check lot status allows ordering
    if lot.lot_status not in [LotStatus.AVAILABLE, LotStatus.PARTIALLY_SOLD]:
        raise HTTPException(
            status_code=400,
            detail=f"Lot is not available for ordering. Status: {lot.lot_status}"
        )

    # Step 5 — reserve the stock
    # This immediately reduces available_kg
    # Prevents double-selling while order is pending
    reserve_stock(db, lot_id, quantity_kg)

    # Step 6 — calculate full price breakdown
    value = calculate_order_value(lot, quantity_kg)

    # Step 7 — determine order type from lot ownership
    if lot.ownership_type == "marinecatch_owned":
        order_type = OrderType.PROCUREMENT
    elif lot.ownership_type == "contract_reserved":
        order_type = OrderType.FULFILLMENT
    else:
        order_type = OrderType.MARKETPLACE

    # Step 8 — create the order record
    order = Order(
        buyer_id          = buyer_id,
        lot_id            = lot_id,
        fisherman_id      = lot.source_user_id,
        order_type        = order_type,
        species           = lot.species,
        landing_site      = lot.landing_site,
        quantity_kg       = quantity_kg,
        price_per_kg      = lot.selling_price_per_kg,
        total_kes         = value["total_buyer_pays_kes"],
        platform_fee_kes  = value["platform_commission_kes"],
        net_to_fisher_kes = value["net_to_seller_kes"],
        commission_rate   = value["commission_rate"],
        delivery_address  = delivery_address,
        notes             = notes,
        status            = OrderStatus.PENDING_PAYMENT,
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# ── GET SINGLE ORDER ──────────────────────────────────────────────
def get_order(db: Session, order_id: int) -> Order:
    """Fetch one order by ID. Raises 404 if not found."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order {order_id} not found"
        )
    return order


# ── GET ORDERS BY BUYER ───────────────────────────────────────────
def get_orders_by_buyer(
    db:       Session,
    buyer_id: int,
    status:   Optional[str] = None,
    skip:     int           = 0,
    limit:    int           = 50,
) -> List[Order]:
    """
    All orders placed by a specific buyer.
    Used by buyer dashboard and order history.
    """
    query = db.query(Order).filter(Order.buyer_id == buyer_id)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


# ── GET ORDERS BY LOT ─────────────────────────────────────────────
def get_orders_by_lot(db: Session, lot_id: int) -> List[Order]:
    """
    All orders against a specific inventory lot.
    Used by admin and fisher to track lot sales.
    Supports partial lot sales — multiple orders per lot.
    """
    return db.query(Order).filter(
        Order.lot_id == lot_id
    ).order_by(Order.created_at.desc()).all()


# ── CANCEL ORDER ──────────────────────────────────────────────────
def cancel_order(
    db:         Session,
    order_id:   int,
    cancelled_by: str = "buyer",
) -> Order:
    """
    Cancel an order and release reserved stock.

    Only allowed if order has not been dispatched.
    Once fish is in transit, cancellation needs admin intervention.

    Real world:
    Hotel cancels order before pickup arranged.
    Stock goes back to available for other buyers.
    """
    order = get_order(db, order_id)

    # Cannot cancel if already dispatched or delivered
    if order.status in [
        OrderStatus.DISPATCHED,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot cancel order in status: {order.status.value}. "
                f"Contact MarineCatch admin for assistance."
            )
        )

    # Already cancelled
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )

    # Release the reserved stock back to available
    if order.lot_id and order.quantity_kg:
        release_stock(db, order.lot_id, order.quantity_kg)

    # Update order status
    order.status     = OrderStatus.CANCELLED
    order.updated_by = cancelled_by

    db.commit()
    db.refresh(order)
    return order


# ── CONFIRM ORDER ─────────────────────────────────────────────────
def confirm_order(
    db:           Session,
    order_id:     int,
    confirmed_by: str = "admin",
) -> Order:
    """
    MarineCatch admin confirms the order.
    Moves from PENDING_PAYMENT to CONFIRMED.

    In Phase 2 this will be triggered automatically
    by M-Pesa payment webhook, not manually.

    For now: admin confirms after verifying payment
    was received (cash or manual M-Pesa check).
    """
    order = get_order(db, order_id)

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Only PENDING_PAYMENT orders can be confirmed. "
                f"Current status: {order.status.value}"
            )
        )

    order.status     = OrderStatus.CONFIRMED
    order.updated_by = confirmed_by

    db.commit()
    db.refresh(order)
    return order


# ── UPDATE ORDER STATUS ───────────────────────────────────────────
def update_order_status(
    db:         Session,
    order_id:   int,
    new_status: OrderStatus,
    updated_by: str = "admin",
) -> Order:
    """
    General status update for admin use.
    Used for: PREPARING → DISPATCHED → DELIVERED → COMPLETED

    Validates status transitions — prevents jumping
    from PENDING_PAYMENT directly to COMPLETED.
    """
    order = get_order(db, order_id)

    # Define allowed transitions
    allowed_transitions = {
        OrderStatus.PENDING_PAYMENT: [
            OrderStatus.CONFIRMED,
            OrderStatus.CANCELLED,
            OrderStatus.PAYMENT_FAILED,
        ],
        OrderStatus.CONFIRMED: [
            OrderStatus.PREPARING,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.PREPARING: [
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.DISPATCHED: [
            OrderStatus.DELIVERED,
        ],
        OrderStatus.DELIVERED: [
            OrderStatus.COMPLETED,
            OrderStatus.REFUNDED,
        ],
        OrderStatus.PAYMENT_FAILED: [
            OrderStatus.CANCELLED,
            OrderStatus.PENDING_PAYMENT,
        ],
    }

    allowed = allowed_transitions.get(order.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot move order from {order.status.value} "
                f"to {new_status.value}. "
                f"Allowed next states: {[s.value for s in allowed]}"
            )
        )

    order.status     = new_status
    order.updated_by = updated_by

    db.commit()
    db.refresh(order)
    return order