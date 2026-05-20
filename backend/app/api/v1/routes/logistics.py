# app/api/v1/routes/logistics.py
#
# WHY THIS FILE EXISTS:
# HTTP layer for all logistics operations.
# Zones, hubs, shipments, IoT updates.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.logistics import ShipmentStatus
from app.services.logistics_service import (
    get_all_zones,
    get_zone_by_code,
    validate_order_for_zone,
    get_all_hubs,
    suggest_hub_for_zone,
    create_shipment,
    update_shipment_status,
    update_iot_readings,
    get_shipment_by_order,
    get_shipment_by_reference,
)

router = APIRouter(prefix="/logistics", tags=["Logistics"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class ShipmentCreate(BaseModel):
    order_id:               int
    origin_hub_code:        str
    destination_zone_code:  str
    delivery_address:       str
    delivery_contact_name:  Optional[str]  = None
    delivery_contact_phone: Optional[str]  = None
    provider_code:          Optional[str]  = None
    driver_name:            Optional[str]  = None
    driver_phone:           Optional[str]  = None
    vehicle_reg:            Optional[str]  = None
    delivery_distance_km:   Optional[float] = None
    delivery_cost_kes:      Optional[float] = None
    notes:                  Optional[str]  = None


class StatusUpdate(BaseModel):
    status:     str
    notes:      Optional[str] = None


class IoTUpdate(BaseModel):
    temperature_celsius: Optional[float] = None
    humidity_percent:    Optional[float] = None
    current_lat:         Optional[float] = None
    current_lng:         Optional[float] = None


# ── ZONES ─────────────────────────────────────────────────────────

@router.get("/zones")
def list_zones(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    List all delivery zones.
    Public — buyers use this to check if their area is served.
    """
    zones = get_all_zones(db, active_only=active_only)
    return [
        {
            "zone_code":              z.zone_code,
            "zone_name":              z.zone_name,
            "description":            z.description,
            "counties":               z.counties,
            "status":                 z.status,
            "min_order_kg":           z.min_order_kg,
            "min_order_value_kes":    z.min_order_value_kes,
            "base_delivery_fee_kes":  z.base_delivery_fee_kes,
            "per_kg_fee_kes":         z.per_kg_fee_kes,
            "estimated_delivery_days": z.estimated_delivery_days,
            "same_day_available":     z.same_day_available,
            "cold_chain_supported":   z.cold_chain_supported,
        }
        for z in zones
    ]


@router.get("/zones/validate")
def validate_zone(
    zone_code:   str,
    quantity_kg: float = Query(gt=0),
    order_value: float = Query(gt=0),
    db: Session = Depends(get_db),
):
    """
    Check if an order meets zone requirements.
    Call before confirming delivery to a zone.
    """
    return validate_order_for_zone(db, zone_code, quantity_kg, order_value)


# ── HUBS ──────────────────────────────────────────────────────────

@router.get("/hubs")
def list_hubs(
    active_only: bool = Query(True),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All fulfillment hubs. Admin and staff only."""
    hubs = get_all_hubs(db, active_only=active_only)
    return [
        {
            "hub_code":                h.hub_code,
            "hub_name":                h.hub_name,
            "hub_type":                h.hub_type,
            "region":                  h.region,
            "town":                    h.town,
            "has_cold_storage":        h.has_cold_storage,
            "cold_storage_capacity_kg": h.cold_storage_capacity_kg,
            "can_dispatch":            h.can_dispatch,
            "serves_zones":            h.serves_zones,
            "is_active":               h.is_active,
        }
        for h in hubs
    ]


@router.get("/hubs/suggest")
def suggest_hubs(
    zone_code:   str,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Suggest which hubs can fulfill an order for a zone.
    Admin uses this when assigning shipments.
    """
    hubs = suggest_hub_for_zone(db, zone_code)
    if not hubs:
        return {
            "zone_code": zone_code,
            "message":   "No active hubs found for this zone",
            "hubs":      []
        }
    return {
        "zone_code": zone_code,
        "hubs": [
            {
                "hub_code":         h.hub_code,
                "hub_name":         h.hub_name,
                "hub_type":         h.hub_type,
                "town":             h.town,
                "has_cold_storage": h.has_cold_storage,
            }
            for h in hubs
        ]
    }


# ── SHIPMENTS ─────────────────────────────────────────────────────

@router.post("/shipments", status_code=201)
def create_new_shipment(
    payload:     ShipmentCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin creates a shipment for a confirmed order.
    Assigns hub, zone, driver, and vehicle.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    shipment = create_shipment(
        db=                    db,
        order_id=              payload.order_id,
        origin_hub_code=       payload.origin_hub_code,
        destination_zone_code= payload.destination_zone_code,
        delivery_address=      payload.delivery_address,
        delivery_contact_name= payload.delivery_contact_name,
        delivery_contact_phone= payload.delivery_contact_phone,
        provider_code=         payload.provider_code,
        driver_name=           payload.driver_name,
        driver_phone=          payload.driver_phone,
        vehicle_reg=           payload.vehicle_reg,
        delivery_distance_km=  payload.delivery_distance_km,
        delivery_cost_kes=     payload.delivery_cost_kes,
        assigned_by=           current_user.name,
        notes=                 payload.notes,
    )

    return {
        "success":             True,
        "shipment_reference":  shipment.shipment_reference,
        "order_id":            shipment.order_id,
        "origin_hub_id":       shipment.origin_hub_id,
        "destination_zone_id": shipment.destination_zone_id,
        "status":              shipment.status,
        "estimated_delivery":  shipment.estimated_delivery_at,
        "driver_name":         shipment.driver_name,
        "vehicle_reg":         shipment.vehicle_reg,
        "message":             f"Shipment {shipment.shipment_reference} created"
    }


@router.get("/shipments/order/{order_id}")
def get_order_shipment(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Get shipment details for an order."""
    shipment = get_shipment_by_order(db, order_id)
    if not shipment:
        raise HTTPException(
            status_code=404,
            detail=f"No shipment found for order {order_id}"
        )
    return {
        "shipment_reference":    shipment.shipment_reference,
        "order_id":              shipment.order_id,
        "status":                shipment.status,
        "delivery_address":      shipment.delivery_address,
        "estimated_delivery_at": shipment.estimated_delivery_at,
        "actual_delivery_at":    shipment.actual_delivery_at,
        "driver_name":           shipment.driver_name,
        "driver_phone":          shipment.driver_phone,
        "vehicle_reg":           shipment.vehicle_reg,
        "delivery_cost_kes":     shipment.delivery_cost_kes,
        "cold_chain_status":     shipment.cold_chain_status,
        "temperature_celsius":   shipment.temperature_celsius,
        "humidity_percent":      shipment.humidity_percent,
        "current_lat":           shipment.current_lat,
        "current_lng":           shipment.current_lng,
        "last_location_update":  shipment.last_location_update,
    }


@router.patch("/shipments/{shipment_id}/status")
def update_status(
    shipment_id: int,
    payload:     StatusUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Update shipment status. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        new_status = ShipmentStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}"
        )

    shipment = update_shipment_status(
        db, shipment_id, new_status,
        updated_by=current_user.name,
        notes=payload.notes
    )

    return {
        "success":            True,
        "shipment_reference": shipment.shipment_reference,
        "status":             shipment.status,
        "actual_delivery_at": shipment.actual_delivery_at,
    }


@router.patch("/shipments/{shipment_id}/iot")
def update_iot(
    shipment_id: int,
    payload:     IoTUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Update IoT readings for a shipment.
    Currently manual — later automated via IoT devices.
    Automatically detects cold chain breaches.
    """
    shipment = update_iot_readings(
        db=                  db,
        shipment_id=         shipment_id,
        temperature_celsius= payload.temperature_celsius,
        humidity_percent=    payload.humidity_percent,
        current_lat=         payload.current_lat,
        current_lng=         payload.current_lng,
    )

    alert = None
    if shipment.cold_chain_status.value == "breach":
        alert = f"COLD CHAIN BREACH — Temperature {shipment.temperature_celsius}°C exceeds threshold {shipment.temperature_threshold}°C"
    elif shipment.cold_chain_status.value == "warning":
        alert = f"WARNING — Temperature {shipment.temperature_celsius}°C approaching threshold"

    return {
        "success":            True,
        "shipment_reference": shipment.shipment_reference,
        "temperature_celsius": shipment.temperature_celsius,
        "humidity_percent":   shipment.humidity_percent,
        "cold_chain_status":  shipment.cold_chain_status,
        "alert":              alert,
        "last_update":        shipment.last_location_update,
    }