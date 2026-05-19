# app/models/logistics.py
#
# WHY THIS FILE EXISTS:
# Logistics infrastructure for MarineCatch Africa.
# Models the physical movement of seafood from landing sites
# to buyers across Kenya and eventually East Africa.
#
# Phase 3 MVP models:
# - DeliveryZone: fulfillment economics corridors
# - FulfillmentHub: regional hubs and partner locations
# - LogisticsProvider: transporters and couriers
# - Shipment: physical movement of fish (IoT-ready)
#
# Architecture principle:
# Build IoT-ready fields now, populate manually first.
# GPS, temperature, humidity — nullable today, automated later.

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class ZoneStatus(str, enum.Enum):
    ACTIVE       = "active"        # Fully operational
    COMING_SOON  = "coming_soon"   # Planned, not yet serving
    NOT_SERVED   = "not_served"    # Outside current coverage
    SUSPENDED    = "suspended"     # Temporarily halted


class HubType(str, enum.Enum):
    MARINECATCH_OWNED  = "marinecatch_owned"   # MC cold storage
    PARTNER_HUB        = "partner_hub"         # Eldoret partner etc
    COLLECTION_POINT   = "collection_point"    # Drop-off point
    LANDING_SITE       = "landing_site"        # Fishing landing site
    EXPORT_FACILITY    = "export_facility"     # Export processing


class ShipmentStatus(str, enum.Enum):
    PENDING      = "pending"       # Created, not yet picked up
    PICKED_UP    = "picked_up"     # Collected from hub
    IN_TRANSIT   = "in_transit"    # On the way to buyer
    AT_HUB       = "at_hub"        # Arrived at intermediate hub
    OUT_FOR_DELIVERY = "out_for_delivery"  # Last mile
    DELIVERED    = "delivered"     # Buyer received
    FAILED       = "failed"        # Delivery failed
    RETURNED     = "returned"      # Returned to hub


class ColdChainStatus(str, enum.Enum):
    INTACT       = "intact"        # Temperature maintained
    BREACH       = "breach"        # Temperature exceeded
    WARNING      = "warning"       # Approaching threshold
    UNKNOWN      = "unknown"       # No data yet


# ── DELIVERY ZONE ─────────────────────────────────────────────────

class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id              = Column(Integer, primary_key=True, index=True)
    zone_name       = Column(String(100), unique=True, nullable=False, index=True)
    # e.g. "Coast Corridor", "Nairobi Metro", "Eastern Corridor"

    zone_code       = Column(String(20), unique=True, nullable=False)
    # e.g. "COAST", "NBI", "EASTERN"

    description     = Column(Text, nullable=True)
    # Human readable coverage description

    counties        = Column(String(500), nullable=True)
    # Comma-separated: "Mombasa, Kwale, Kilifi, Malindi"

    status          = Column(
        SAEnum(ZoneStatus, name="zonestatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=ZoneStatus.ACTIVE,
        nullable=False
    )

    # ── ORDER ECONOMICS ───────────────────────────────────────
    min_order_kg        = Column(Float, nullable=True)
    min_order_value_kes = Column(Float, nullable=True)
    base_delivery_fee_kes = Column(Float, default=0.0, nullable=True)
    per_kg_fee_kes      = Column(Float, default=0.0, nullable=True)

    # ── DELIVERY TIMING ───────────────────────────────────────
    estimated_delivery_days = Column(Integer, nullable=True)
    # Typical days from dispatch to delivery

    same_day_available  = Column(Boolean, default=False, nullable=False)
    # Can we do same-day delivery in this zone?

    # ── COLD CHAIN ────────────────────────────────────────────
    cold_chain_supported = Column(Boolean, default=True, nullable=False)
    # Does this zone have cold chain capability?

    max_transit_hours   = Column(Integer, nullable=True)
    # Maximum acceptable transit time for fresh fish

    # ── METADATA ──────────────────────────────────────────────
    is_active   = Column(Boolean, default=True, nullable=False)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DeliveryZone {self.zone_code} — {self.zone_name}>"


# ── FULFILLMENT HUB ───────────────────────────────────────────────

class FulfillmentHub(Base):
    __tablename__ = "fulfillment_hubs"

    id          = Column(Integer, primary_key=True, index=True)
    hub_name    = Column(String(100), unique=True, nullable=False, index=True)
    # e.g. "Mombasa Main Hub", "Eldoret Partner Hub"

    hub_code    = Column(String(20), unique=True, nullable=False)
    # e.g. "MBA-001", "ELD-001"

    hub_type    = Column(
        SAEnum(HubType, name="hubtype", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=HubType.MARINECATCH_OWNED
    )

    # ── LOCATION ──────────────────────────────────────────────
    region      = Column(String(100), nullable=True)
    county      = Column(String(100), nullable=True)
    town        = Column(String(100), nullable=True)
    address     = Column(String(300), nullable=True)
    gps_lat     = Column(Float, nullable=True)
    gps_lng     = Column(Float, nullable=True)

    # ── OPERATOR ──────────────────────────────────────────────
    operator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Links to User — MarineCatch staff or partner

    operator_name    = Column(String(100), nullable=True)
    operator_phone   = Column(String(20), nullable=True)

    # ── CAPABILITIES ──────────────────────────────────────────
    has_cold_storage    = Column(Boolean, default=False, nullable=False)
    cold_storage_capacity_kg = Column(Float, nullable=True)
    can_dispatch        = Column(Boolean, default=True, nullable=False)
    can_receive         = Column(Boolean, default=True, nullable=False)

    # ── ZONES SERVED ──────────────────────────────────────────
    serves_zones        = Column(String(500), nullable=True)
    # Comma-separated zone codes: "COAST,NBI,EASTERN"

    # ── METADATA ──────────────────────────────────────────────
    is_active   = Column(Boolean, default=True, nullable=False)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    operator = relationship("User", foreign_keys=[operator_user_id])

    def __repr__(self):
        return f"<FulfillmentHub {self.hub_code} — {self.hub_name}>"


# ── LOGISTICS PROVIDER ────────────────────────────────────────────

class LogisticsProvider(Base):
    __tablename__ = "logistics_providers"

    id              = Column(Integer, primary_key=True, index=True)
    provider_name   = Column(String(100), nullable=False, index=True)
    provider_code   = Column(String(20), unique=True, nullable=False)

    contact_name    = Column(String(100), nullable=True)
    contact_phone   = Column(String(20), nullable=True)
    contact_email   = Column(String(255), nullable=True)

    # ── CAPABILITIES ──────────────────────────────────────────
    has_refrigerated_vehicles = Column(Boolean, default=False)
    serves_zones    = Column(String(500), nullable=True)
    base_rate_kes   = Column(Float, nullable=True)
    per_km_rate_kes = Column(Float, nullable=True)

    is_active   = Column(Boolean, default=True, nullable=False)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<LogisticsProvider {self.provider_code} — {self.provider_name}>"


# ── SHIPMENT ──────────────────────────────────────────────────────

class Shipment(Base):
    __tablename__ = "shipments"

    id                  = Column(Integer, primary_key=True, index=True)
    shipment_reference  = Column(String(50), unique=True, nullable=False, index=True)
    # Format: MC-SHP-YYYYMMDD-XXXXX

    order_id            = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    origin_hub_id       = Column(Integer, ForeignKey("fulfillment_hubs.id"), nullable=True)
    destination_zone_id = Column(Integer, ForeignKey("delivery_zones.id"), nullable=True)
    provider_id         = Column(Integer, ForeignKey("logistics_providers.id"), nullable=True)

    status = Column(
        SAEnum(ShipmentStatus, name="shipmentstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=ShipmentStatus.PENDING,
        nullable=False,
        index=True
    )

    # ── DELIVERY DETAILS ──────────────────────────────────────
    delivery_address        = Column(String(300), nullable=True)
    delivery_contact_name   = Column(String(100), nullable=True)
    delivery_contact_phone  = Column(String(20), nullable=True)
    estimated_delivery_at   = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_at      = Column(DateTime(timezone=True), nullable=True)
    delivery_distance_km    = Column(Float, nullable=True)

    # ── COST ──────────────────────────────────────────────────
    delivery_cost_kes       = Column(Float, nullable=True)
    fuel_cost_kes           = Column(Float, nullable=True)
    driver_fee_kes          = Column(Float, nullable=True)

    # ── IOT FIELDS — nullable now, automated later ─────────────
    # Temperature monitoring
    temperature_celsius     = Column(Float, nullable=True)
    temperature_min_celsius = Column(Float, nullable=True)
    temperature_max_celsius = Column(Float, nullable=True)
    temperature_threshold   = Column(Float, default=4.0, nullable=True)
    # Standard: fresh fish must stay below 4°C

    # Humidity monitoring
    humidity_percent        = Column(Float, nullable=True)
    humidity_min_percent    = Column(Float, nullable=True)
    humidity_max_percent    = Column(Float, nullable=True)
    # Optimal: 90-95% for fresh fish

    # GPS tracking
    current_lat             = Column(Float, nullable=True)
    current_lng             = Column(Float, nullable=True)
    last_location_update    = Column(DateTime(timezone=True), nullable=True)

    # Cold chain integrity
    cold_chain_status = Column(
        SAEnum(ColdChainStatus, name="coldchainstatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=ColdChainStatus.UNKNOWN,
        nullable=True
    )
    cold_chain_breach_at    = Column(DateTime(timezone=True), nullable=True)
    door_open_count         = Column(Integer, default=0, nullable=True)
    # How many times refrigeration unit was opened

    # ── AUDIT ─────────────────────────────────────────────────
    assigned_by             = Column(String(100), nullable=True)
    driver_name             = Column(String(100), nullable=True)
    driver_phone            = Column(String(20), nullable=True)
    vehicle_reg             = Column(String(20), nullable=True)
    notes                   = Column(Text, nullable=True)
    receiver_name           = Column(String(100), nullable=True)
    receiver_signature      = Column(String(200), nullable=True)

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    order        = relationship("Order", foreign_keys=[order_id])
    origin_hub   = relationship("FulfillmentHub", foreign_keys=[origin_hub_id])
    zone         = relationship("DeliveryZone", foreign_keys=[destination_zone_id])
    provider     = relationship("LogisticsProvider", foreign_keys=[provider_id])

    def __repr__(self):
        return f"<Shipment {self.shipment_reference} status={self.status}>"