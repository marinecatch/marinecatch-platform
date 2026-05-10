# app/api/v1/routes/orders.py
#
# PROTECTED ENDPOINTS:
# POST /orders        — buyers only
# GET  /orders/me     — logged in user sees their own orders
# PATCH /orders/status — fisher confirms, buyer confirms delivery

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
from app.database.memory_store import (
    get_listing_by_id,
    update_listing,
    create_order,
    get_orders_by_buyer,
    get_orders_by_fisher
)
from app.api.v1.routes.users import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

# ── COMMISSION CALCULATOR ─────────────────────────────────────────
def calculate_commission(total_kes: float) -> dict:
    """
    MarineCatch tiered commission.
    < 5,000 KES    → 3.5%
    5,000–50,000   → 2.5%
    > 50,000       → 1.5%
    """
    if total_kes < 5000:       rate = 0.035
    elif total_kes < 50000:    rate = 0.025
    else:                      rate = 0.015

    fee = round(total_kes * rate, 2)
    return {
        "commission_rate":   f"{rate * 100}%",
        "platform_fee_kes":  fee,
        "net_to_fisher_kes": round(total_kes - fee, 2)
    }

# ── PLACE ORDER — buyers only ─────────────────────────────────────
@router.post("/", status_code=201)
def place_order(
    listing_id: int,
    quantity_kg: float,
    delivery_address: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)  # ← requires token
):
    """
    Place an order. REQUIRES: Login token + buyer role.

    Example:
    Neptune Hotels logs in → orders 30kg tuna from Bakari Usi.
    Abdalla Masudi (fisher) tries → gets 403 Forbidden.
    """
    # Role check
    if current_user["role"] not in ["buyer"]:
        raise HTTPException(
            status_code=403,
            detail=f"Only buyers can place orders. Your role: {current_user['role']}"
        )

    listing = get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if not listing.get("is_available"):
        raise HTTPException(status_code=400, detail="Listing no longer available")

    if quantity_kg > listing["weight_kg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only {listing['weight_kg']}kg available. You requested {quantity_kg}kg"
        )

    total_kes  = round(quantity_kg * listing["price_per_kg"], 2)
    commission = calculate_commission(total_kes)

    order = create_order({
        "listing_id":        listing_id,
        "buyer_id":          current_user["id"],
        "buyer_name":        current_user["name"],
        "fisher_id":         listing["fisher_id"],
        "fisher_name":       listing["fisher_name"],
        "species":           listing["species"],
        "landing_site":      listing["landing_site"],
        "quantity_kg":       quantity_kg,
        "price_per_kg":      listing["price_per_kg"],
        "total_kes":         total_kes,
        "platform_fee_kes":  commission["platform_fee_kes"],
        "net_to_fisher_kes": commission["net_to_fisher_kes"],
        "commission_rate":   commission["commission_rate"],
        "delivery_address":  delivery_address,
        "notes":             notes,
        "status":            "pending"
    })

    # Reduce available stock
    remaining = listing["weight_kg"] - quantity_kg
    update_listing(listing_id, {
        "weight_kg":    remaining,
        "is_available": remaining > 0
    })

    return {
        "success": True,
        "order":   order,
        "summary": {
            "total_kes":         total_kes,
            "platform_fee_kes":  commission["platform_fee_kes"],
            "net_to_fisher_kes": commission["net_to_fisher_kes"],
            "commission_rate":   commission["commission_rate"],
        },
        "message": f"Order placed. {listing['fisher_name']} will confirm shortly."
    }

# ── MY ORDERS — logged in user ────────────────────────────────────
@router.get("/me")
def get_my_orders(
    current_user: dict = Depends(get_current_user)
):
    """
    Get orders for the logged-in user.
    Fisher sees orders placed ON their listings.
    Buyer sees orders THEY placed.
    """
    role = current_user["role"]
    uid  = current_user["id"]

    if role == "fisher" or role == "supplier":
        orders = get_orders_by_fisher(uid)
        total_earned = sum(
            o["net_to_fisher_kes"] for o in orders
            if o["status"] == "delivered"
        )
        return {
            "role":             role,
            "name":             current_user["name"],
            "orders":           orders,
            "count":            len(orders),
            "total_earned_kes": total_earned
        }

    elif role == "buyer":
        orders = get_orders_by_buyer(uid)
        total_spent = sum(o["total_kes"] for o in orders)
        return {
            "role":           role,
            "name":           current_user["name"],
            "orders":         orders,
            "count":          len(orders),
            "total_spent_kes": total_spent
        }

    return {"orders": [], "count": 0}

# ── UPDATE STATUS ─────────────────────────────────────────────────
@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Update order through lifecycle.
    Fisher: pending → confirmed → dispatched
    Buyer:  dispatched → delivered
    """
    from app.database.memory_store import _orders

    VALID_TRANSITIONS = {
        "pending":    ["confirmed", "cancelled"],
        "confirmed":  ["dispatched", "cancelled"],
        "dispatched": ["delivered", "cancelled"],
        "delivered":  [],
        "cancelled":  []
    }

    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Access control
    role = current_user["role"]
    uid  = current_user["id"]

    if role in ["fisher", "supplier"] and order["fisher_id"] != uid:
        raise HTTPException(status_code=403, detail="Not your order")

    if role == "buyer" and order["buyer_id"] != uid:
        raise HTTPException(status_code=403, detail="Not your order")

    allowed = VALID_TRANSITIONS.get(order["status"], [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move from '{order['status']}' to '{new_status}'. Allowed: {allowed}"
        )

    order["status"]     = new_status
    order["updated_at"] = datetime.utcnow().isoformat()
    order["updated_by"] = current_user["name"]

    return {
        "success":    True,
        "order_id":   order_id,
        "new_status": new_status,
        "updated_by": current_user["name"],
        "message":    f"Order {order_id} is now {new_status}"
    }

# ── GET SINGLE ORDER ──────────────────────────────────────────────
@router.get("/{order_id}")
def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get one order. Must be buyer or fisher on that order."""
    from app.database.memory_store import _orders

    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    uid = current_user["id"]
    if uid not in [order["buyer_id"], order["fisher_id"]]:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own orders"
        )

    return order