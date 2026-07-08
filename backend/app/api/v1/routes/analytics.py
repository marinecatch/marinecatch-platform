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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from app.database.connection import get_db
from app.models.fisheries_data import HistoricalLanding, Species, LandingSite
from app.models.inventory_lot import InventoryLot, LotStatus
from app.models.order import Order
from app.models.user import User

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
