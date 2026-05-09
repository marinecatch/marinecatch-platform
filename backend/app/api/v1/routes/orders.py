# app/api/v1/routes/orders.py
#
# WHY THIS FILE EXISTS:
# Handles the full order lifecycle.
# Neptune Hotels orders tuna from Bakari Usi.
# Samaki Samaki orders octopus from Abdalla Masudi.
#
# Flow:
# Buyer places order → commission calculated →
# Fisher confirms → dispatched → delivered

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from app.database.memory_store import (
    get_listing_by_id,
    update_listing,
    create_order,
    get_orders_by_buyer,
    get_orders_by_fisher
)

router = APIRouter(prefix="/orders", tags=["Orders"])

# ── COMMISSION CALCULATOR ─────────────────────────────────────────
def calculate_commission(total_kes: float) -> dict:
    """
    MarineCatch platform commission tiers.
    Small orders pay more % — large orders get discount.

    < 5,000 KES    → 3.5%
    5,000–50,000   → 2.5%
    > 50,000       → 1.5%
    """
    if total_kes < 5000:
        rate = 0.035
    elif total_kes < 50000:
        rate = 0.025
    else:
        rate = 0.015

    fee = round(total_kes * rate, 2)
    return {
        "commission_rate":    f"{rate * 100}%",
        "platform_fee_kes":   fee,
        "net_to_fisher_kes":  round(total_kes - fee, 2)
    }

# ── PLACE ORDER ───────────────────────────────────────────────────
@router.post("/", status_code=201)
def place_order(
    listing_id: int,
    quantity_kg: float,
    buyer_id: int,
    buyer_name: str,
    delivery_address: str,
    notes: Optional[str] = None
):
    """
    Buyer places an order on a fish listing.

    Example:
    Neptune Hotels orders 30kg tuna from Bakari Usi.
    Total = 30 x 780 = KES 23,400
    Commission (2.5%) = KES 585
    Net to Bakari = KES 22,815
    """
    # 1. Find the listing
    listing = get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )

    # 2. Check it is still available
    if not listing.get("is_available"):
        raise HTTPException(
            status_code=400,
            detail="This listing is no longer available"
        )

    # 3. Check enough quantity
    if quantity_kg > listing["weight_kg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only {listing['weight_kg']}kg available. You requested {quantity_kg}kg"
        )

    # 4. Calculate totals
    total_kes  = round(quantity_kg * listing["price_per_kg"], 2)
    commission = calculate_commission(total_kes)

    # 5. Create the order
    order = create_order({
        "listing_id":        listing_id,
        "buyer_id":          buyer_id,
        "buyer_name":        buyer_name,
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

    # 6. Reduce available quantity
    remaining = listing["weight_kg"] - quantity_kg
    if remaining <= 0:
        update_listing(listing_id, {
            "is_available": False,
            "weight_kg": 0
        })
    else:
        update_listing(listing_id, {"weight_kg": remaining})

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

# ── GET MY ORDERS (BUYER) ─────────────────────────────────────────
@router.get("/buyer/{buyer_id}")
def get_buyer_orders(buyer_id: int):
    """
    Get all orders for a buyer.
    Example: Neptune Hotels sees all their tuna/lobster orders.
    """
    orders = get_orders_by_buyer(buyer_id)
    if not orders:
        return {"orders": [], "count": 0}
    return {"orders": orders, "count": len(orders)}

# ── GET MY ORDERS (FISHER) ────────────────────────────────────────
@router.get("/fisher/{fisher_id}")
def get_fisher_orders(fisher_id: int):
    """
    Get all orders for a fisher.
    Example: Bakari Usi sees who ordered his tuna.
    """
    orders = get_orders_by_fisher(fisher_id)
    if not orders:
        return {"orders": [], "count": 0}

    total_earnings = sum(o["net_to_fisher_kes"] for o in orders
                        if o["status"] == "delivered")
    return {
        "orders":         orders,
        "count":          len(orders),
        "total_earned_kes": total_earnings
    }

# ── UPDATE ORDER STATUS ───────────────────────────────────────────
@router.patch("/{order_id}/status")
def update_order_status(order_id: int, new_status: str, updated_by: str):
    """
    Update order status through lifecycle.

    Valid transitions:
    pending → confirmed  (fisher confirms)
    confirmed → dispatched (fisher sends)
    dispatched → delivered (buyer confirms receipt)
    any → cancelled
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

    allowed = VALID_TRANSITIONS.get(order["status"], [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move from '{order['status']}' to '{new_status}'. Allowed: {allowed}"
        )

    order["status"]     = new_status
    order["updated_at"] = datetime.utcnow().isoformat()
    order["updated_by"] = updated_by

    return {
        "success": True,
        "order_id": order_id,
        "new_status": new_status,
        "message": f"Order {order_id} is now {new_status}"
    }

# ── GET SINGLE ORDER ──────────────────────────────────────────────
@router.get("/{order_id}")
def get_order(order_id: int):
    """Get full details of one order."""
    from app.database.memory_store import _orders
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order