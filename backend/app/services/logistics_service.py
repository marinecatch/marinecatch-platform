# app/services/logistics_service.py
#
# WHY THIS FILE EXISTS:
# Business logic for logistics operations.
# - Zone lookup and validation
# - Hub assignment suggestions
# - Shipment creation and tracking
# - Delivery cost calculation
# - Cold chain monitoring

from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from app.models.logistics import (
    DeliveryZone, FulfillmentHub, LogisticsProvider,
    Shipment, ZoneStatus, ShipmentStatus, ColdChainStatus
)
from app.models.order import Order


# ── ZONE LOOKUP ───────────────────────────────────────────────────

def get_all_zones(db: Session, active_only: bool = True) -> List[DeliveryZone]:
    query = db.query(DeliveryZone)
    if active_only:
        query = query.filter(DeliveryZone.status == ZoneStatus.ACTIVE)
    return query.order_by(DeliveryZone.zone_name).all()


def get_zone_by_code(db: Session, zone_code: str) -> Optional[DeliveryZone]:
    return db.query(DeliveryZone).filter(
        DeliveryZone.zone_code == zone_code.upper()
    ).first()


def validate_order_for_zone(
    db:          Session,
    zone_code:   str,
    quantity_kg: float,
    order_value: float,
) -> dict:
    """
    Check if an order meets the minimum requirements for a zone.
    Called before confirming delivery to a zone.
    """
    zone = get_zone_by_code(db, zone_code)
    if not zone:
        return {"valid": False, "reason": f"Zone {zone_code} not found"}

    if zone.status == ZoneStatus.NOT_SERVED:
        return {"valid": False, "reason": f"{zone.zone_name} is not currently served"}

    if zone.status == ZoneStatus.COMING_SOON:
        return {"valid": False, "reason": f"{zone.zone_name} is coming soon — not yet active"}

    if zone.min_order_kg and quantity_kg < zone.min_order_kg:
        return {
            "valid":  False,
            "reason": f"Minimum order for {zone.zone_name} is {zone.min_order_kg}kg. You ordered {quantity_kg}kg"
        }

    if zone.min_order_value_kes and order_value < zone.min_order_value_kes:
        return {
            "valid":  False,
            "reason": f"Minimum order value for {zone.zone_name} is KES {zone.min_order_value_kes}"
        }

    return {
        "valid":                  True,
        "zone_name":              zone.zone_name,
        "estimated_delivery_days": zone.estimated_delivery_days,
        "same_day_available":     zone.same_day_available,
        "cold_chain_supported":   zone.cold_chain_supported,
        "delivery_fee_kes":       zone.base_delivery_fee_kes,
    }


# ── HUB LOOKUP ────────────────────────────────────────────────────

def get_all_hubs(db: Session, active_only: bool = True) -> List[FulfillmentHub]:
    query = db.query(FulfillmentHub)
    if active_only:
        query = query.filter(FulfillmentHub.is_active == True)
    return query.order_by(FulfillmentHub.hub_name).all()


def get_hub_by_code(db: Session, hub_code: str) -> Optional[FulfillmentHub]:
    return db.query(FulfillmentHub).filter(
        FulfillmentHub.hub_code == hub_code.upper()
    ).first()


def suggest_hub_for_zone(db: Session, zone_code: str) -> List[FulfillmentHub]:
    """
    Suggest which hubs can fulfill an order for a given zone.
    Admin uses this to decide which hub to assign.
    """
    hubs = db.query(FulfillmentHub).filter(
        FulfillmentHub.is_active == True,
        FulfillmentHub.can_dispatch == True,
    ).all()

    matching = []
    for hub in hubs:
        if hub.serves_zones:
            served = [z.strip() for z in hub.serves_zones.split(",")]
            if zone_code.upper() in served:
                matching.append(hub)

    return matching


# ── SHIPMENT CREATION ─────────────────────────────────────────────

def generate_shipment_reference(db: Session) -> str:
    today    = datetime.now(timezone.utc).strftime("%Y%m%d")
    count    = db.query(Shipment).filter(
        Shipment.shipment_reference.like(f"MC-SHP-{today}-%")
    ).count()
    sequence = str(count + 1).zfill(5)
    return f"MC-SHP-{today}-{sequence}"


def create_shipment(
    db:                    Session,
    order_id:              int,
    origin_hub_code:       str,
    destination_zone_code: str,
    delivery_address:      str,
    delivery_contact_name: Optional[str]  = None,
    delivery_contact_phone: Optional[str] = None,
    provider_code:         Optional[str]  = None,
    driver_name:           Optional[str]  = None,
    driver_phone:          Optional[str]  = None,
    vehicle_reg:           Optional[str]  = None,
    delivery_distance_km:  Optional[float] = None,
    delivery_cost_kes:     Optional[float] = None,
    assigned_by:           str            = "admin",
    notes:                 Optional[str]  = None,
) -> Shipment:
    """
    Create a shipment for an order.
    Admin assigns hub, zone, provider, and driver.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    hub = get_hub_by_code(db, origin_hub_code)
    if not hub:
        raise HTTPException(
            status_code=404,
            detail=f"Hub {origin_hub_code} not found"
        )

    zone = get_zone_by_code(db, destination_zone_code)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Zone {destination_zone_code} not found"
        )

    provider = None
    if provider_code:
        provider = db.query(LogisticsProvider).filter(
            LogisticsProvider.provider_code == provider_code.upper()
        ).first()

    ref = generate_shipment_reference(db)

    # Estimate delivery date
    estimated_delivery = None
    if zone.estimated_delivery_days:
        estimated_delivery = datetime.now(timezone.utc) + timedelta(
            days=zone.estimated_delivery_days
        )

    shipment = Shipment(
        shipment_reference     = ref,
        order_id               = order_id,
        origin_hub_id          = hub.id,
        destination_zone_id    = zone.id,
        provider_id            = provider.id if provider else None,
        status                 = ShipmentStatus.PENDING,
        delivery_address       = delivery_address,
        delivery_contact_name  = delivery_contact_name,
        delivery_contact_phone = delivery_contact_phone,
        estimated_delivery_at  = estimated_delivery,
        delivery_distance_km   = delivery_distance_km,
        delivery_cost_kes      = delivery_cost_kes,
        driver_name            = driver_name,
        driver_phone           = driver_phone,
        vehicle_reg            = vehicle_reg,
        assigned_by            = assigned_by,
        cold_chain_status      = ColdChainStatus.UNKNOWN,
        temperature_threshold  = 4.0,
        notes                  = notes,
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


# ── SHIPMENT STATUS UPDATE ────────────────────────────────────────

def update_shipment_status(
    db:          Session,
    shipment_id: int,
    new_status:  ShipmentStatus,
    updated_by:  str = "admin",
    notes:       Optional[str] = None,
) -> Shipment:
    """Update shipment status through lifecycle."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.status = new_status

    if new_status == ShipmentStatus.DELIVERED:
        shipment.actual_delivery_at = datetime.now(timezone.utc)

    if notes:
        existing = shipment.notes or ""
        shipment.notes = f"{existing} | {updated_by}: {notes}".strip(" |")

    db.commit()
    db.refresh(shipment)
    return shipment


# ── IOT UPDATE ────────────────────────────────────────────────────

def update_iot_readings(
    db:                 Session,
    shipment_id:        int,
    temperature_celsius: Optional[float] = None,
    humidity_percent:   Optional[float]  = None,
    current_lat:        Optional[float]  = None,
    current_lng:        Optional[float]  = None,
) -> Shipment:
    """
    Update IoT sensor readings for a shipment.
    Currently called manually — later automated via IoT devices.
    Checks for cold chain breach automatically.
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    now = datetime.now(timezone.utc)

    if temperature_celsius is not None:
        shipment.temperature_celsius = temperature_celsius
        if shipment.temperature_min_celsius is None or temperature_celsius < shipment.temperature_min_celsius:
            shipment.temperature_min_celsius = temperature_celsius
        if shipment.temperature_max_celsius is None or temperature_celsius > shipment.temperature_max_celsius:
            shipment.temperature_max_celsius = temperature_celsius

        # Check cold chain breach
        threshold = shipment.temperature_threshold or 4.0
        if temperature_celsius > threshold:
            if shipment.cold_chain_status != ColdChainStatus.BREACH:
                shipment.cold_chain_breach_at = now
            shipment.cold_chain_status = ColdChainStatus.BREACH
        elif temperature_celsius > threshold - 1:
            shipment.cold_chain_status = ColdChainStatus.WARNING
        else:
            if shipment.cold_chain_status not in [ColdChainStatus.BREACH]:
                shipment.cold_chain_status = ColdChainStatus.INTACT

    if humidity_percent is not None:
        shipment.humidity_percent = humidity_percent
        if shipment.humidity_min_percent is None or humidity_percent < shipment.humidity_min_percent:
            shipment.humidity_min_percent = humidity_percent
        if shipment.humidity_max_percent is None or humidity_percent > shipment.humidity_max_percent:
            shipment.humidity_max_percent = humidity_percent

    if current_lat is not None:
        shipment.current_lat = current_lat
    if current_lng is not None:
        shipment.current_lng = current_lng

    if current_lat or current_lng or temperature_celsius or humidity_percent:
        shipment.last_location_update = now

    db.commit()
    db.refresh(shipment)
    return shipment


# ── GET SHIPMENT ──────────────────────────────────────────────────

def get_shipment_by_order(db: Session, order_id: int) -> Optional[Shipment]:
    return db.query(Shipment).filter(
        Shipment.order_id == order_id
    ).order_by(Shipment.created_at.desc()).first()


def get_shipment_by_reference(db: Session, reference: str) -> Optional[Shipment]:
    return db.query(Shipment).filter(
        Shipment.shipment_reference == reference
    ).first()