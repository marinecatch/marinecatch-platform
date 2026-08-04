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


# ── PUBLIC TRACKING (no auth) ───────────────────────────────────

@router.get("/track/{order_id}")
def track_order_public(
    order_id: int,
    phone:    str = Query(..., description="Phone number used for the order"),
    db:       Session = Depends(get_db),
):
    """
    Public order tracking — no login required.
    Customer provides order ID + their phone number to verify identity.
    Used by ad-driven customers who haven't registered yet.
    """
    from app.models.order import Order
    from app.models.user import User
    from app.models.transport_job import TransportJob
    from app.models.custody_event import CustodyEvent
    from app.models.trade_receivable import TradeReceivable

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    if not buyer or not buyer.phone or phone[-9:] not in buyer.phone:
        raise HTTPException(
            status_code=403,
            detail="Phone number does not match this order. Please check and try again."
        )

    # Get transport jobs for this order
    jobs = db.query(TransportJob).filter(
        TransportJob.order_id == order_id
    ).order_by(TransportJob.sequence_number.asc()).all()

    # Get custody events
    custody = db.query(CustodyEvent).join(
        TransportJob, CustodyEvent.transport_job_id == TransportJob.id
    ).filter(TransportJob.order_id == order_id).order_by(
        CustodyEvent.event_at.asc()
    ).all() if jobs else []

    # Get payment status
    receivable = db.query(TradeReceivable).filter(
        TradeReceivable.order_id == order_id
    ).first()

    status_timeline = {
        "pending_payment": 1, "confirmed": 2, "preparing": 3,
        "dispatched": 4, "delivered": 5, "completed": 6,
    }
    current_step = status_timeline.get(order.status.value, 1)

    return {
        "order_id":     order.id,
        "species":      order.species,
        "quantity_kg":  order.quantity_kg,
        "total_kes":    order.total_kes,
        "status":       order.status.value,
        "current_step": current_step,
        "delivery_address": order.delivery_address,
        "created_at":   order.created_at,
        "payment_status": receivable.status if receivable else "pending",
        "jobs": [
            {
                "job_type":    j.job_type,
                "pickup":      j.pickup_location,
                "destination": j.destination_location,
                "status":      j.status,
                "scheduled_departure": j.scheduled_departure,
                "actual_arrival": j.actual_arrival,
            } for j in jobs
        ],
        "timeline": [
            {
                "event": c.event_type,
                "location": c.location,
                "at": c.event_at,
            } for c in custody
        ],
    }

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
async def api_update_status(
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

    # Send WhatsApp notification to buyer
    try:
        from app.services.whatsapp_service import send_text
        from app.models.user import User as UserModel

        buyer = db.query(UserModel).filter(UserModel.id == order.buyer_id).first()
        if buyer and buyer.phone:
            status_messages = {
                "confirmed": (
                    f"✅ *Order Confirmed*\n\n"
                    f"Your order #{order.id} for {order.quantity_kg}kg "
                    f"{order.species} has been confirmed.\n\n"
                    f"Track your order: https://marinecatchafrica.com/track\n"
                    f"MarineCatch Africa 🐟"
                ),
                "preparing": (
                    f"🔧 *Order Being Prepared*\n\n"
                    f"Order #{order.id} — {order.quantity_kg}kg {order.species}\n"
                    f"is being prepared for dispatch.\n\n"
                    f"Track your order: https://marinecatchafrica.com/track\n"
                    f"MarineCatch Africa 🐟"
                ),
                "dispatched": (
                    f"🚚 *Order Dispatched*\n\n"
                    f"Order #{order.id} — {order.quantity_kg}kg {order.species}\n"
                    f"is on its way to you.\n\n"
                    f"Track your order: https://marinecatchafrica.com/track\n"
                    f"MarineCatch Africa 🐟"
                ),
                "delivered": (
                    f"📦 *Order Delivered*\n\n"
                    f"Order #{order.id} — {order.quantity_kg}kg {order.species}\n"
                    f"has been delivered. Thank you for choosing MarineCatch!\n\n"
                    f"MarineCatch Africa 🐟"
                ),
                "completed": (
                    f"✅ *Order Completed*\n\n"
                    f"Order #{order.id} is now complete.\n"
                    f"Thank you for your business!\n\n"
                    f"MarineCatch Africa 🐟"
                ),
                "cancelled": (
                    f"❌ *Order Cancelled*\n\n"
                    f"Order #{order.id} has been cancelled.\n"
                    f"Contact us if you have questions.\n\n"
                    f"MarineCatch Africa 🐟"
                ),
            }
            message = status_messages.get(order.status.value)
            if message:
                await send_text(buyer.phone, message)
    except Exception as e:
        # Don't fail the status update if WhatsApp notification fails
        print(f"WhatsApp notification failed: {e}")

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

@router.get("/admin/summary")
def orders_summary(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Real aggregate order stats for the admin dashboard.
    Not paginated — actual totals, not a page count.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    from app.models.order import Order, OrderStatus
    from sqlalchemy import func
    from datetime import datetime, timezone

    UNPAID = [OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED, OrderStatus.PAYMENT_FAILED]

    total_orders = db.query(func.count(Order.id)).scalar() or 0

    total_revenue = db.query(func.sum(Order.total_kes)).filter(
        ~Order.status.in_(UNPAID)
    ).scalar() or 0

    pending_count = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.PENDING_PAYMENT
    ).scalar() or 0

    today = datetime.now(timezone.utc).date()
    today_orders = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0

    today_revenue = db.query(func.sum(Order.total_kes)).filter(
        func.date(Order.created_at) == today,
        ~Order.status.in_(UNPAID)
    ).scalar() or 0

    return {
        "total_orders":          total_orders,
        "total_revenue_kes":     round(total_revenue, 0),
        "pending_payment_count": pending_count,
        "today_orders":          today_orders,
        "today_revenue_kes":     round(today_revenue, 0),
    }