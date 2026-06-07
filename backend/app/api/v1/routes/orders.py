# app/api/v1/routes/orders.py
#
# WHY THIS FILE EXISTS:
# HTTP layer for all order operations.
# Thin layer — validates input, calls order_service, returns response.
# No business logic lives here.
#
# Public endpoints: none — all orders require login
#
# Protected endpoints:
#   POST   /orders/                        → place an order
#   GET    /orders/me                      → buyer sees their orders
#   GET    /orders/{order_id}              → get single order
#   POST   /orders/{order_id}/cancel       → cancel an order
#   POST   /orders/{order_id}/confirm      → admin confirms order
#   PATCH  /orders/{order_id}/status       → admin updates status

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.order import OrderStatus
from app.services.order_service import (
    place_order,
    get_order,
    get_orders_by_buyer,
    get_orders_by_lot,
    cancel_order,
    confirm_order,
    update_order_status,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    lot_id:           int
    quantity_kg:      float = Field(gt=0)
    delivery_address: Optional[str] = None
    notes:            Optional[str] = None


class StatusUpdate(BaseModel):
    status:     str
    updated_by: Optional[str] = None


# ── PLACE ORDER ───────────────────────────────────────────────────

@router.post("/", status_code=201)
def api_place_order(
    payload:      OrderCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Buyer places an order against an inventory lot.
    Any registered user can place an order.

    What happens:
    - Stock reserved immediately
    - Full price breakdown calculated
    - Order created with status PENDING_PAYMENT
    - Awaits admin confirmation until M-Pesa live (Phase 2)

    Example:
    Neptune Hotels orders 20kg tuna from Bakari's lot.
    """
    order = place_order(
        db=               db,
        buyer_id=         current_user.id,
        lot_id=           payload.lot_id,
        quantity_kg=      payload.quantity_kg,
        delivery_address= payload.delivery_address,
        notes=            payload.notes,
    )

    return {
        "success":          True,
        "order_id":         order.id,
        "lot_id":           order.lot_id,
        "species":          order.species,
        "quantity_kg":      order.quantity_kg,
        "price_per_kg":     order.price_per_kg,
        "total_kes":        order.total_kes,
        "platform_fee_kes": order.platform_fee_kes,
        "net_to_fisher_kes":order.net_to_fisher_kes,
        "status":           order.status,
        "message":          (
            f"Order placed successfully. "
            f"{order.quantity_kg}kg {order.species} reserved. "
            f"Total: KES {order.total_kes}. "
            f"Awaiting payment confirmation."
        )
    }


# ── MY ORDERS ─────────────────────────────────────────────────────

@router.get("/me")
def api_get_my_orders(
    status:      Optional[str] = Query(None),
    skip:        int           = Query(0, ge=0),
    limit:       int           = Query(20, le=100),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Logged-in buyer sees all their orders.
    Optionally filter by status.
    """
    orders = get_orders_by_buyer(
        db,
        buyer_id= current_user.id,
        status=   status,
        skip=     skip,
        limit=    limit,
    )

    return {
        "buyer":       current_user.name,
        "total_orders": len(orders),
        "orders": [
            {
                "order_id":     o.id,
                "lot_id":       o.lot_id,
                "species":      o.species,
                "quantity_kg":  o.quantity_kg,
                "total_kes":    o.total_kes,
                "status":       o.status,
                "landing_site": o.landing_site,
                "created_at":   o.created_at,
            }
            for o in orders
        ]
    }


# ── SINGLE ORDER ──────────────────────────────────────────────────

@router.get("/{order_id}")
def api_get_order(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Get full details of one order.
    Buyer can only see their own orders.
    Admin can see all orders.
    """
    order = get_order(db, order_id)

    # Security: buyer can only see their own orders
    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own orders"
        )

    return {
        "order_id":          order.id,
        "lot_id":            order.lot_id,
        "species":           order.species,
        "landing_site":      order.landing_site,
        "quantity_kg":       order.quantity_kg,
        "price_per_kg":      order.price_per_kg,
        "total_kes":         order.total_kes,
        "platform_fee_kes":  order.platform_fee_kes,
        "net_to_fisher_kes": order.net_to_fisher_kes,
        "commission_rate":   order.commission_rate,
        "delivery_address":  order.delivery_address,
        "status":            order.status,
        "order_type":        order.order_type,
        "notes":             order.notes,
        "created_at":        order.created_at,
        "updated_at":        order.updated_at,
        "updated_by":        order.updated_by,
    }


# ── CANCEL ORDER ──────────────────────────────────────────────────

@router.post("/{order_id}/cancel")
def api_cancel_order(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Cancel an order and release reserved stock.
    Buyer can cancel their own order.
    Admin can cancel any order.
    Not allowed once order is dispatched.
    """
    order = get_order(db, order_id)

    # Security: buyer can only cancel their own orders
    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only cancel your own orders"
        )

    order = cancel_order(
        db=           db,
        order_id=     order_id,
        cancelled_by= current_user.name,
    )

    return {
        "success":    True,
        "order_id":   order.id,
        "status":     order.status,
        "message":    f"Order {order.id} cancelled. Stock released back to available."
    }


# ── CONFIRM ORDER (admin) ─────────────────────────────────────────

@router.post("/{order_id}/confirm")
def api_confirm_order(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin confirms order after verifying payment received.
    In Phase 2 this will be triggered by M-Pesa webhook automatically.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can confirm orders"
        )

    order = confirm_order(
        db=           db,
        order_id=     order_id,
        confirmed_by= current_user.name,
    )

    return {
        "success":  True,
        "order_id": order.id,
        "status":   order.status,
        "message":  f"Order {order.id} confirmed by {current_user.name}"
    }


# ── UPDATE STATUS (admin) ─────────────────────────────────────────

@router.patch("/{order_id}/status")
def api_update_status(
    order_id:    int,
    payload:     StatusUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin moves order through lifecycle.
    CONFIRMED → PREPARING → DISPATCHED → DELIVERED → COMPLETED

    Validates transitions — cannot skip stages.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can update order status"
        )

    try:
        new_status = OrderStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}"
        )

    order = update_order_status(
        db=         db,
        order_id=   order_id,
        new_status= new_status,
        updated_by= payload.updated_by or current_user.name,
    )

    return {
        "success":  True,
        "order_id": order.id,
        "status":   order.status,
        "message":  f"Order {order.id} updated to {order.status.value}"
    }


# ── ORDERS BY LOT (admin/fisher) ──────────────────────────────────

@router.get("/lot/{lot_id}")
def api_get_orders_by_lot(
    lot_id:      int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    All orders against a specific lot.
    Used by admin and fisher to track sales.
    """
    orders = get_orders_by_lot(db, lot_id)

    return {
        "lot_id":       lot_id,
        "total_orders": len(orders),
        "orders": [
            {
                "order_id":    o.id,
                "buyer_id":    o.buyer_id,
                "quantity_kg": o.quantity_kg,
                "total_kes":   o.total_kes,
                "status":      o.status,
                "created_at":  o.created_at,
            }
            for o in orders
        ]
    }
    # ── LIST ALL ORDERS (admin) ───────────────────────────────────────

@router.get("/admin/all")
def api_list_all_orders(
    skip:  int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """List all orders for admin dashboard."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    from app.models.order import Order
    from app.models.user import User

    orders = db.query(Order).order_by(
        Order.created_at.desc()
    ).offset(skip).limit(limit).all()

    result = []
    for order in orders:
        buyer = db.query(User).filter(User.id == order.buyer_id).first()
        result.append({
            "order_id":      order.id,
            "species":       order.species,
            "quantity_kg":   order.quantity_kg,
            "total_kes":     order.total_kes,
            "status":        order.status.value,
            "order_type":    order.order_type.value if order.order_type else None,
            "buyer_name":    buyer.name if buyer else None,
            "lpo_reference": order.lpo_reference,
            "created_at":    order.created_at,
        })

    return {"total": len(result), "orders": result}