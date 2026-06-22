# app/services/fee_service.py
#
# WHY THIS FILE EXISTS:
# Single source of truth for all fee calculations.
# Every order, payment, and invoice uses this service.
#
# Fee stack for a MarineCatch transaction:
# 1. Fish value (quantity × price)
# 2. Platform commission (tiered by value)
# 3. Cold storage fee (per kg per day)
# 4. Handling fee (per lot, prorated)
# 5. QA fee (per lot, prorated)
# 6. Logistics fee (by distance tier)
# 7. Tax/VAT (future)
#
# Rules-based: different ownership types,
# species, grades, and routes produce different economics.
#
# This becomes the pricing engine for:
# - marketplace orders
# - MarineCatch-owned inventory
# - processor contracts
# - export orders
# - future dynamic pricing

from app.models.inventory_lot import InventoryLot, OwnershipType


# ── MARKETPLACE COMMISSION TIERS ──────────────────────────────────
# OOC11 recommendation: seller 10-14%, buyer 3-5%
# Tiered by order value — lower rate for larger orders

MARKETPLACE_SELLER_COMMISSION = [
    (5_000,        0.14),   # Under KES 5,000 → 14%
    (50_000,       0.12),   # KES 5,000–50,000 → 12%
    (200_000,      0.11),   # KES 50,000–200,000 → 11%
    (float('inf'), 0.10),   # Over KES 200,000 → 10%
]

MARKETPLACE_BUYER_FEE = [
    (5_000,        0.05),   # Under KES 5,000 → 5%
    (50_000,       0.04),   # KES 5,000–50,000 → 4%
    (200_000,      0.035),  # KES 50,000–200,000 → 3.5%
    (float('inf'), 0.03),   # Over KES 200,000 → 3%
]

# ── ENTERPRISE COMMISSION TIERS ───────────────────────────────────
# For verified enterprise buyers (processors, exporters, hotels)
# Lower rates + subscription model

ENTERPRISE_SELLER_COMMISSION = [
    (50_000,       0.08),   # Under KES 50,000 → 8%
    (200_000,      0.06),   # KES 50,000–200,000 → 6%
    (500_000,      0.05),   # KES 200,000–500,000 → 5%
    (float('inf'), 0.04),   # Over KES 500,000 → 4%
]

ENTERPRISE_BUYER_FEE = [
    (50_000,       0.03),   # Under KES 50,000 → 3%
    (200_000,      0.025),  # KES 50,000–200,000 → 2.5%
    (float('inf'), 0.02),   # Over KES 200,000 → 2%
]

# ── SUBSCRIPTION TIERS ────────────────────────────────────────────
# Monthly subscription for enterprise accounts
# Reduces per-transaction fees

SUBSCRIPTION_TIERS = {
    "basic":      {"monthly_kes": 0,       "discount": 0.0,  "label": "Free"},
    "standard":   {"monthly_kes": 5_000,   "discount": 0.15, "label": "Standard"},
    "enterprise": {"monthly_kes": 15_000,  "discount": 0.30, "label": "Enterprise"},
    "api":        {"monthly_kes": 25_000,  "discount": 0.40, "label": "API Partner"},
}

# ── LEGACY TIERS (kept for backward compatibility) ─────────────────
COMMISSION_TIERS = [
    (5_000,        0.035),
    (50_000,       0.025),
    (200_000,      0.020),
    (float('inf'), 0.015),
]

# ── LOGISTICS TIERS ───────────────────────────────────────────────
# Delivery cost by distance
# Will be replaced by DeliveryZone model in Phase 3

LOGISTICS_TIERS = [
    (50,   150),    # Under 50km → KES 150 flat
    (100,  300),    # 50–100km → KES 300
    (200,  600),    # 100–200km → KES 600
    (400,  1200),   # 200–400km → KES 1,200
    (float('inf'), 2500),  # Over 400km → KES 2,500
]


# ── EXPORT GRADE UPLIFT ───────────────────────────────────────────
# Export-grade orders attract higher QA fees
EXPORT_QA_MULTIPLIER = 2.5


# ── COMMISSION CALCULATOR ─────────────────────────────────────────
def calculate_commission(
    fish_value_kes: float,
    ownership_type: str,
    buyer_tier: str = "marketplace",
    subscription: str = "basic"
) -> dict:
    """
    Calculate platform commission based on OOC11 tiered model.

    buyer_tier:
      marketplace  → standard rates (10-14% seller, 3-5% buyer)
      enterprise   → reduced rates (4-8% seller, 2-3% buyer)

    subscription:
      basic        → no discount
      standard     → 15% discount on fees
      enterprise   → 30% discount on fees
      api          → 40% discount on fees

    MarineCatch-owned: no commission — margin built into price.
    """
    # MarineCatch-owned — no commission
    if ownership_type in [
        OwnershipType.MARINECATCH_OWNED.value,
        "marinecatch_owned"
    ]:
        return {
            "commission_rate":     "0%",
            "commission_rate_pct": 0.0,
            "commission_kes":      0.0,
            "buyer_fee_rate":      "0%",
            "buyer_fee_kes":       0.0,
            "total_platform_kes":  0.0,
            "note": "MarineCatch-owned: margin built into selling price"
        }

    # Select tier tables
    if buyer_tier == "enterprise":
        seller_tiers = ENTERPRISE_SELLER_COMMISSION
        buyer_tiers  = ENTERPRISE_BUYER_FEE
    else:
        seller_tiers = MARKETPLACE_SELLER_COMMISSION
        buyer_tiers  = MARKETPLACE_BUYER_FEE

    # Find seller commission rate
    seller_rate = seller_tiers[-1][1]
    for threshold, rate in seller_tiers:
        if fish_value_kes < threshold:
            seller_rate = rate
            break

    # Find buyer fee rate
    buyer_rate = buyer_tiers[-1][1]
    for threshold, rate in buyer_tiers:
        if fish_value_kes < threshold:
            buyer_rate = rate
            break

    # Apply subscription discount
    discount = SUBSCRIPTION_TIERS.get(subscription, {}).get("discount", 0.0)
    seller_rate = round(seller_rate * (1 - discount), 4)
    buyer_rate  = round(buyer_rate  * (1 - discount), 4)

    seller_commission_kes = round(fish_value_kes * seller_rate, 2)
    buyer_fee_kes         = round(fish_value_kes * buyer_rate, 2)
    total_platform_kes    = round(seller_commission_kes + buyer_fee_kes, 2)

    return {
        "commission_rate":      f"{seller_rate * 100:.1f}%",
        "commission_rate_pct":  seller_rate,
        "commission_kes":       seller_commission_kes,
        "buyer_fee_rate":       f"{buyer_rate * 100:.1f}%",
        "buyer_fee_rate_pct":   buyer_rate,
        "buyer_fee_kes":        buyer_fee_kes,
        "total_platform_kes":   total_platform_kes,
        "buyer_tier":           buyer_tier,
        "subscription":         subscription,
        "note": (
            f"{buyer_tier.title()} tier — "
            f"seller {seller_rate*100:.1f}% + "
            f"buyer {buyer_rate*100:.1f}%"
            + (f" ({int(discount*100)}% subscription discount)" if discount else "")
        )
    }


def get_subscription_info(subscription: str = "basic") -> dict:
    """Return subscription tier details."""
    tier = SUBSCRIPTION_TIERS.get(subscription, SUBSCRIPTION_TIERS["basic"])
    return {
        "tier":        subscription,
        "label":       tier["label"],
        "monthly_kes": tier["monthly_kes"],
        "discount_pct": int(tier["discount"] * 100),
    }


# ── STORAGE FEE CALCULATOR ────────────────────────────────────────
def calculate_storage_fee(
    lot: InventoryLot,
    quantity_kg: float,
    storage_days: int = 1,
) -> dict:
    """
    Calculate cold storage fee for a given quantity and duration.
    Fee = quantity_kg × fee_per_kg_per_day × storage_days
    """
    if not lot.cold_storage_fee_per_kg_per_day:
        return {
            "storage_fee_kes": 0.0,
            "storage_days":    0,
            "note":            "No cold storage fee for this lot"
        }

    storage_fee = round(
        quantity_kg * lot.cold_storage_fee_per_kg_per_day * storage_days, 2
    )

    return {
        "storage_fee_kes":      storage_fee,
        "storage_days":         storage_days,
        "fee_per_kg_per_day":   lot.cold_storage_fee_per_kg_per_day,
        "note":                 f"Cold storage: {storage_days} day(s)"
    }


# ── HANDLING FEE CALCULATOR ───────────────────────────────────────
def calculate_handling_fee(
    lot: InventoryLot,
    quantity_kg: float,
) -> dict:
    """
    Prorate handling fee by quantity ordered vs total lot weight.
    """
    if not lot.handling_fee_kes:
        return {"handling_fee_kes": 0.0}

    proportion   = quantity_kg / lot.weight_kg if lot.weight_kg > 0 else 1
    handling_fee = round(lot.handling_fee_kes * proportion, 2)

    return {
        "handling_fee_kes": handling_fee,
        "proportion":       round(proportion, 4),
        "note":             f"{quantity_kg}kg of {lot.weight_kg}kg lot"
    }


# ── QA FEE CALCULATOR ────────────────────────────────────────────
def calculate_qa_fee(
    lot: InventoryLot,
    quantity_kg: float,
    is_export_grade: bool = False,
) -> dict:
    """
    Prorate QA fee by quantity. Apply export multiplier if needed.
    """
    if not lot.qa_fee_kes:
        return {"qa_fee_kes": 0.0}

    proportion = quantity_kg / lot.weight_kg if lot.weight_kg > 0 else 1
    base_qa    = lot.qa_fee_kes * proportion

    if is_export_grade:
        base_qa *= EXPORT_QA_MULTIPLIER

    qa_fee = round(base_qa, 2)

    return {
        "qa_fee_kes":      qa_fee,
        "is_export_grade": is_export_grade,
        "note":            "Export QA rate applied" if is_export_grade else "Standard QA rate"
    }


# ── LOGISTICS FEE CALCULATOR ──────────────────────────────────────
def calculate_logistics_fee(
    delivery_distance_km: float = None,
    quantity_kg: float = 0,
) -> dict:
    """
    Calculate logistics cost by distance tier.
    Phase 3 will replace this with DeliveryZone model.
    """
    if not delivery_distance_km:
        return {
            "logistics_fee_kes": 0.0,
            "note":              "Self-pickup or no distance provided"
        }

    # Find applicable tier
    base_fee = LOGISTICS_TIERS[-1][1]
    for threshold, fee in LOGISTICS_TIERS:
        if delivery_distance_km < threshold:
            base_fee = fee
            break

    # Add per-kg surcharge for heavy orders
    per_kg_surcharge = 0.0
    if quantity_kg > 100:
        per_kg_surcharge = round((quantity_kg - 100) * 2, 2)

    total_logistics = round(base_fee + per_kg_surcharge, 2)

    return {
        "logistics_fee_kes":   total_logistics,
        "base_fee_kes":        base_fee,
        "per_kg_surcharge":    per_kg_surcharge,
        "distance_km":         delivery_distance_km,
        "note":                f"Distance tier: {delivery_distance_km}km"
    }


# ── FULL FEE BREAKDOWN ────────────────────────────────────────────
def calculate_full_fee_breakdown(
    lot:                  InventoryLot,
    quantity_kg:          float,
    storage_days:         int   = 1,
    delivery_distance_km: float = None,
    is_export_grade:      bool  = False,
) -> dict:
    """
    Complete fee breakdown for an order.
    Single function called by order service, payment service, and invoice service.

    Returns every component separately for transparency.
    Buyers see this before confirming an order.
    Finance team uses this for reconciliation.
    """
    # Base fish value
    fish_value_kes = round(quantity_kg * lot.selling_price_per_kg, 2)

    # All fee components
    commission  = calculate_commission(fish_value_kes, lot.ownership_type)
    storage     = calculate_storage_fee(lot, quantity_kg, storage_days)
    handling    = calculate_handling_fee(lot, quantity_kg)
    qa          = calculate_qa_fee(lot, quantity_kg, is_export_grade)
    logistics   = calculate_logistics_fee(delivery_distance_km, quantity_kg)

    # Totals
    total_fees = round(
        commission["commission_kes"]
        + storage["storage_fee_kes"]
        + handling["handling_fee_kes"]
        + qa["qa_fee_kes"]
        + logistics["logistics_fee_kes"],
        2
    )

    total_buyer_pays = round(fish_value_kes + total_fees, 2)

    # What fisher/supplier receives
    net_to_seller = round(fish_value_kes - commission["commission_kes"], 2)

    # MarineCatch revenue from this transaction
    marinecatch_revenue = round(
        commission["commission_kes"]
        + storage["storage_fee_kes"]
        + handling["handling_fee_kes"]
        + qa["qa_fee_kes"]
        + logistics["logistics_fee_kes"],
        2
    )

    # MarineCatch margin for owned inventory
    marinecatch_margin = None
    if lot.ownership_type == OwnershipType.MARINECATCH_OWNED.value and lot.purchase_price_per_kg:
        procurement_cost   = round(quantity_kg * lot.purchase_price_per_kg, 2)
        marinecatch_margin = round(fish_value_kes - procurement_cost, 2)

    return {
        "quantity_kg":           quantity_kg,
        "price_per_kg":          lot.selling_price_per_kg,
        "fish_value_kes":        fish_value_kes,
        "ownership_type":        lot.ownership_type,
        "fees": {
            "commission":        commission,
            "storage":           storage,
            "handling":          handling,
            "qa":                qa,
            "logistics":         logistics,
            "total_fees_kes":    total_fees,
        },
        "totals": {
            "total_buyer_pays_kes":  total_buyer_pays,
            "net_to_seller_kes":     net_to_seller,
            "marinecatch_revenue_kes": marinecatch_revenue,
            "marinecatch_margin_kes":  marinecatch_margin,
        },
        "is_export_grade":       is_export_grade,
        "storage_days":          storage_days,
        "delivery_distance_km":  delivery_distance_km,
    }