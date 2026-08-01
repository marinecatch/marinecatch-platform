# app/api/v1/routes/analytics.py
#
# WHY THIS FILE EXISTS:
# Market intelligence and fisheries analytics endpoints.
# Powers the analytics dashboard and demo intelligence.
#
# Data sources:
# 1. HistoricalLanding — BMU records 2024-2025
# 2. InventoryLot — live platform data
# 3. Orders — transaction data
#
# Endpoints:
# GET /analytics/species-summary     — top species by volume/value
# GET /analytics/monthly-trends      — monthly catch trends
# GET /analytics/price-intelligence  — price ranges by species
# GET /analytics/platform-summary    — live platform stats

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from app.database.connection import get_db
from app.models.fisheries_data import HistoricalLanding, Species, LandingSite
from app.models.inventory_lot import InventoryLot, LotStatus
from app.models.order import Order
from app.models.user import User
from app.api.v1.routes.users import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/species-summary")
def species_summary(
    year:          Optional[int] = Query(None),
    landing_site:  Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Top species by volume and value from BMU data.
    Used for: procurement planning, demo intelligence.
    """
    query = db.query(
        HistoricalLanding.species_common,
        HistoricalLanding.species_local,
        HistoricalLanding.category,
        func.sum(HistoricalLanding.weight_kg).label('total_kg'),
        func.sum(HistoricalLanding.value_kes).label('total_value'),
        func.avg(HistoricalLanding.price_per_kg).label('avg_price'),
        func.count(HistoricalLanding.id).label('records'),
    )

    if year:
        query = query.filter(HistoricalLanding.year == year)
    if landing_site:
        query = query.filter(
            HistoricalLanding.landing_site_name.ilike(f"%{landing_site}%")
        )

    results = query.group_by(
        HistoricalLanding.species_common,
        HistoricalLanding.species_local,
        HistoricalLanding.category,
    ).order_by(func.sum(HistoricalLanding.weight_kg).desc()).all()

    return {
        "year":         year or "all",
        "landing_site": landing_site or "all",
        "species": [
            {
                "species":       r.species_common,
                "local_name":    r.species_local,
                "category":      r.category,
                "total_kg":      round(r.total_kg, 1),
                "total_value_kes": round(r.total_value or 0, 0),
                "avg_price_per_kg": round(r.avg_price or 0, 0),
                "data_points":   r.records,
            }
            for r in results
        ]
    }


@router.get("/monthly-trends")
def monthly_trends(
    year:         Optional[int] = Query(None),
    species:      Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Monthly catch volume trends.
    Shows seasonality — September/October peaks visible here.
    """
    query = db.query(
        HistoricalLanding.year,
        HistoricalLanding.month,
        func.sum(HistoricalLanding.weight_kg).label('total_kg'),
        func.sum(HistoricalLanding.value_kes).label('total_value'),
    )

    if year:
        query = query.filter(HistoricalLanding.year == year)
    if species:
        query = query.filter(
            HistoricalLanding.species_common.ilike(f"%{species}%")
        )

    results = query.group_by(
        HistoricalLanding.year,
        HistoricalLanding.month,
    ).order_by(
        HistoricalLanding.year,
        HistoricalLanding.month
    ).all()

    month_names = {
        1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
        7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'
    }

    return {
        "year":    year or "all",
        "species": species or "all",
        "trends": [
            {
                "year":        r.year,
                "month":       r.month,
                "month_name":  month_names.get(r.month, str(r.month)),
                "total_kg":    round(r.total_kg, 1),
                "total_value_kes": round(r.total_value or 0, 0),
            }
            for r in results
        ]
    }


@router.get("/price-intelligence")
def price_intelligence(
    db: Session = Depends(get_db)
):
    """
    Price ranges by species.
    Two data sources:
    1. BMU historical data (Kwale County fisheries records)
    2. Live platform inventory prices
    Both returned separately to avoid species name mismatch.
    """
    # Historical prices from BMU data
    historical = db.query(
        HistoricalLanding.species_common,
        HistoricalLanding.species_local,
        func.avg(HistoricalLanding.price_per_kg).label('bmu_avg'),
        func.min(HistoricalLanding.price_per_kg).label('bmu_min'),
        func.max(HistoricalLanding.price_per_kg).label('bmu_max'),
    ).filter(
        HistoricalLanding.price_per_kg > 0
    ).group_by(
        HistoricalLanding.species_common,
        HistoricalLanding.species_local,
    ).all()

    # Live platform prices — independent of BMU data
    live = db.query(
        InventoryLot.species,
        func.avg(InventoryLot.selling_price_per_kg).label('platform_avg'),
        func.min(InventoryLot.selling_price_per_kg).label('platform_min'),
        func.max(InventoryLot.selling_price_per_kg).label('platform_max'),
        func.sum(InventoryLot.available_kg).label('available_kg'),
        func.count(InventoryLot.id).label('lot_count'),
    ).filter(
        InventoryLot.lot_status == LotStatus.AVAILABLE,
        InventoryLot.selling_price_per_kg > 0,
        InventoryLot.is_active == True,
    ).group_by(InventoryLot.species).all()

    return {
        "bmu_intelligence": [
            {
                "species":      r.species_common,
                "local_name":   r.species_local,
                "avg_kes":      round(r.bmu_avg or 0, 0),
                "min_kes":      round(r.bmu_min or 0, 0),
                "max_kes":      round(r.bmu_max or 0, 0),
                "source":       "Kwale County BMU Records 2024-2025",
            }
            for r in historical
        ],
        "platform_prices": [
            {
                "species":          r.species,
                "platform_avg_kes": round(r.platform_avg or 0, 0),
                "platform_min_kes": round(r.platform_min or 0, 0),
                "platform_max_kes": round(r.platform_max or 0, 0),
                "available_kg":     round(r.available_kg or 0, 1),
                "active_lots":      r.lot_count,
            }
            for r in live
        ],
        "price_intelligence": [
            {
                "species":               r.species,
                "local_name":            None,
                "bmu_avg_kes":           None,
                "platform_avg_kes":      round(r.platform_avg or 0, 0),
                "platform_available_kg": round(r.available_kg or 0, 1),
            }
            for r in live
        ]
    }


@router.get("/platform-summary")
def platform_summary(db: Session = Depends(get_db)):
    """
    Live platform statistics.
    Used for: dashboard, investor demos, landing page.
    """
    total_lots      = db.query(InventoryLot).filter(InventoryLot.is_active == True).count()
    available_lots  = db.query(InventoryLot).filter(
        InventoryLot.lot_status == LotStatus.AVAILABLE
    ).count()
    total_kg        = db.query(func.sum(InventoryLot.available_kg)).filter(
        InventoryLot.lot_status == LotStatus.AVAILABLE
    ).scalar() or 0
    total_value     = db.query(
        func.sum(InventoryLot.available_kg * InventoryLot.selling_price_per_kg)
    ).filter(
        InventoryLot.lot_status == LotStatus.AVAILABLE
    ).scalar() or 0
    total_users     = db.query(User).filter(User.is_active == True).count()
    from sqlalchemy import text
    total_fishers = db.execute(
        text("SELECT COUNT(*) FROM users WHERE LOWER(role::text) LIKE '%fisher%'")
    ).scalar() or 0
    total_orders    = db.query(Order).count()
    species_count   = db.query(InventoryLot.species).filter(
        InventoryLot.is_active == True
    ).distinct().count()

    # BMU data stats
    bmu_records     = db.query(HistoricalLanding).count()
    bmu_total_kg    = db.query(
        func.sum(HistoricalLanding.weight_kg)
    ).scalar() or 0
    bmu_total_value = db.query(
        func.sum(HistoricalLanding.value_kes)
    ).scalar() or 0

    return {
        "platform": {
            "active_lots":       total_lots,
            "available_lots":    available_lots,
            "available_kg":      round(total_kg, 1),
            "inventory_value_kes": round(total_value, 0),
            "active_users":      total_users,
            "fishers":           total_fishers,
            "total_orders":      total_orders,
            "species_traded":    species_count,
        },
        "market_intelligence": {
            "bmu_records":       bmu_records,
            "historical_kg":     round(bmu_total_kg, 1),
            "historical_value_kes": round(bmu_total_value, 0),
            "data_source":       "Kibuyuni BMU — KFS Records 2024-2025",
        }
    }
@router.get("/executive-summary")
def executive_summary(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    CEO-level aggregate view: revenue, GMV, top buyers/fishers,
    species and regional mix. CEO only — sensitive financial data.
    """
    if not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="CEO access only")

    UNPAID = ["pending_payment", "cancelled", "payment_failed"]

    gmv = db.query(func.sum(Order.total_kes)).scalar() or 0

    revenue = db.query(func.sum(Order.total_kes)).filter(
        ~Order.status.in_(UNPAID)
    ).scalar() or 0

    fisher_payouts_owed = db.query(func.sum(Order.net_to_fisher_kes)).filter(
        ~Order.status.in_(UNPAID)
    ).scalar() or 0

    platform_commission = db.query(func.sum(Order.platform_fee_kes)).filter(
        ~Order.status.in_(UNPAID)
    ).scalar() or 0

    top_buyers_q = db.query(
        Order.buyer_id,
        func.sum(Order.total_kes).label("total_spent"),
        func.count(Order.id).label("order_count")
    ).filter(~Order.status.in_(UNPAID)).group_by(Order.buyer_id).order_by(
        func.sum(Order.total_kes).desc()
    ).limit(5).all()

    buyer_ids  = [b.buyer_id for b in top_buyers_q]
    buyers_map = {u.id: u.name for u in db.query(User).filter(User.id.in_(buyer_ids)).all()} if buyer_ids else {}

    top_buyers = [
        {
            "buyer_id":        b.buyer_id,
            "name":            buyers_map.get(b.buyer_id, f"Buyer #{b.buyer_id}"),
            "total_spent_kes": round(b.total_spent, 0),
            "order_count":     b.order_count,
        }
        for b in top_buyers_q
    ]

    top_fishers_q = db.query(
        Order.fisherman_id,
        func.sum(Order.net_to_fisher_kes).label("total_earned"),
        func.count(Order.id).label("order_count")
    ).filter(
        ~Order.status.in_(UNPAID),
        Order.fisherman_id.isnot(None)
    ).group_by(Order.fisherman_id).order_by(
        func.sum(Order.net_to_fisher_kes).desc()
    ).limit(5).all()

    fisher_ids  = [f.fisherman_id for f in top_fishers_q]
    fishers_map = {u.id: u.name for u in db.query(User).filter(User.id.in_(fisher_ids)).all()} if fisher_ids else {}

    top_fishers = [
        {
            "fisher_id":         f.fisherman_id,
            "name":              fishers_map.get(f.fisherman_id, f"Fisher #{f.fisherman_id}"),
            "total_earned_kes":  round(f.total_earned, 0),
            "order_count":       f.order_count,
        }
        for f in top_fishers_q
    ]

    species_q = db.query(
        Order.species,
        func.sum(Order.total_kes).label("revenue"),
        func.sum(Order.quantity_kg).label("kg")
    ).filter(~Order.status.in_(UNPAID)).group_by(Order.species).order_by(
        func.sum(Order.total_kes).desc()
    ).all()

    species_mix = [
        {"species": s.species, "revenue_kes": round(s.revenue, 0), "kg": round(s.kg, 1)}
        for s in species_q
    ]

    region_q = db.query(
        Order.landing_site,
        func.sum(Order.total_kes).label("revenue"),
        func.count(Order.id).label("order_count")
    ).filter(
        ~Order.status.in_(UNPAID),
        Order.landing_site.isnot(None)
    ).group_by(Order.landing_site).order_by(
        func.sum(Order.total_kes).desc()
    ).all()

    regional_mix = [
        {"landing_site": r.landing_site, "revenue_kes": round(r.revenue, 0), "order_count": r.order_count}
        for r in region_q
    ]

    total_users   = db.query(func.count(User.id)).filter(User.is_lead == False).scalar() or 0
    total_fishers = db.query(func.count(User.id)).filter(User.role == "fisher", User.is_lead == False).scalar() or 0
    total_buyers  = db.query(func.count(User.id)).filter(User.role == "buyer", User.is_lead == False).scalar() or 0

    return {
        "gmv_kes":                 round(gmv, 0),
        "revenue_kes":             round(revenue, 0),
        "platform_commission_kes": round(platform_commission, 0),
        "fisher_payouts_owed_kes": round(fisher_payouts_owed, 0),
        "total_users":             total_users,
        "total_fishers":           total_fishers,
        "total_buyers":            total_buyers,
        "top_buyers":              top_buyers,
        "top_fishers":             top_fishers,
        "species_mix":             species_mix,
        "regional_mix":            regional_mix,
    }

@router.get("/liquidity")
def marketplace_liquidity(
    days: int = Query(30, description="Lookback window in days"),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    Marketplace health metrics: how efficiently supply meets demand.
    CEO only. All figures are real, computed from actual lots/orders —
    no fabricated or estimated inputs.

    NOTE: "Buyer Fill Rate" and "Demand Coverage" from classic marketplace
    liquidity models are intentionally excluded — this platform has no
    concept of an unfulfilled buyer request (buyers only see and order
    what's already listed), so there is no real "demand" figure to compare
    supply against yet. Adding that would require a buyer request/wishlist
    feature first.
    """
    if not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="CEO access only")

    from datetime import datetime, timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    UNPAID = ["pending_payment", "cancelled", "payment_failed"]

    # Sell-through rate: how much of what was listed has actually moved
    lots = db.query(InventoryLot).filter(InventoryLot.created_at >= since).all()
    total_listed_kg = sum(l.weight_kg or 0 for l in lots)
    total_available_kg = sum(l.available_kg or 0 for l in lots)
    sold_kg = total_listed_kg - total_available_kg
    sell_through_rate = round((sold_kg / total_listed_kg) * 100, 1) if total_listed_kg > 0 else None

    # Average time to first sale (lot creation -> earliest order against it)
    lot_ids_in_period = [l.id for l in lots]
    time_to_sale_hours = []
    if lot_ids_in_period:
        earliest_orders = db.query(
            Order.lot_id, func.min(Order.created_at).label("first_order_at")
        ).filter(
            Order.lot_id.in_(lot_ids_in_period),
            ~Order.status.in_(UNPAID)
        ).group_by(Order.lot_id).all()

        lot_created_map = {l.id: l.created_at for l in lots}
        for row in earliest_orders:
            lot_created = lot_created_map.get(row.lot_id)
            if lot_created and row.first_order_at:
                delta_hours = (row.first_order_at - lot_created).total_seconds() / 3600
                if delta_hours >= 0:
                    time_to_sale_hours.append(delta_hours)

    avg_time_to_sale_hours = round(sum(time_to_sale_hours) / len(time_to_sale_hours), 1) \
        if time_to_sale_hours else None

    # Order completion rate
    orders_in_period = db.query(Order).filter(Order.created_at >= since).all()
    non_cancelled = [o for o in orders_in_period if o.status not in ("cancelled", "payment_failed")]
    completed = [o for o in non_cancelled if o.status in ("delivered", "completed")]
    completion_rate = round((len(completed) / len(non_cancelled)) * 100, 1) if non_cancelled else None

    # Repeat buyer rate
    buyer_order_counts = db.query(
        Order.buyer_id, func.count(Order.id).label("cnt")
    ).filter(~Order.status.in_(UNPAID)).group_by(Order.buyer_id).all()
    total_buyers_with_orders = len(buyer_order_counts)
    repeat_buyers = len([b for b in buyer_order_counts if b.cnt > 1])
    repeat_buyer_rate = round((repeat_buyers / total_buyers_with_orders) * 100, 1) \
        if total_buyers_with_orders > 0 else None

    # Active sellers / buyers in period
    active_fishers = db.query(func.count(func.distinct(Order.fisherman_id))).filter(
        Order.created_at >= since, ~Order.status.in_(UNPAID)
    ).scalar() or 0
    active_buyers = db.query(func.count(func.distinct(Order.buyer_id))).filter(
        Order.created_at >= since, ~Order.status.in_(UNPAID)
    ).scalar() or 0

    # Composite index — documented, adjustable heuristic, not an industry-standard formula.
    # Scores each component 0-100, then applies weights. Missing components are
    # excluded from the weighted average rather than scored as zero, so early-stage
    # thin data doesn't unfairly tank the score.
    components = []
    if sell_through_rate is not None:
        components.append((sell_through_rate, 0.35))
    if avg_time_to_sale_hours is not None:
        # Faster = better. 6hrs=100, 24hrs=75, 72hrs=50, 168hrs(1wk)=25, beyond=10
        if avg_time_to_sale_hours <= 6: speed_score = 100
        elif avg_time_to_sale_hours <= 24: speed_score = 75
        elif avg_time_to_sale_hours <= 72: speed_score = 50
        elif avg_time_to_sale_hours <= 168: speed_score = 25
        else: speed_score = 10
        components.append((speed_score, 0.30))
    if completion_rate is not None:
        components.append((completion_rate, 0.20))
    if repeat_buyer_rate is not None:
        components.append((repeat_buyer_rate, 0.15))

    liquidity_index = round(
        sum(score * weight for score, weight in components) / sum(w for _, w in components), 1
    ) if components else None

    return {
        "period_days":              days,
        "sell_through_rate_pct":    sell_through_rate,
        "avg_time_to_sale_hours":   avg_time_to_sale_hours,
        "order_completion_rate_pct": completion_rate,
        "repeat_buyer_rate_pct":    repeat_buyer_rate,
        "active_fishers":           active_fishers,
        "active_buyers":            active_buyers,
        "liquidity_index":          liquidity_index,
        "liquidity_index_note":     "Composite of sell-through rate (35%), speed to sale (30%), order completion (20%), repeat buyers (15%). Weights are a starting heuristic — adjust as real data accumulates.",
    }