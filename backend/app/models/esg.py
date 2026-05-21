# app/models/esg.py
#
# WHY THIS FILE EXISTS:
# Fisheries intelligence infrastructure for MarineCatch Africa.
# Not just ESG compliance forms — operational data that powers:
# - traceability from catch to consumer
# - export compliance (KEBS, EU, HACCP)
# - sustainability scoring
# - fisher impact profiles
# - BMU co-management data
# - eco-labelling
# - blue economy reporting
#
# Architecture principle:
# Capture rich operational data at every touchpoint.
# Compliance export templates draw from this same dataset.
# Never build separate ESG forms — embed into operations.
#
# Models:
# - CatchEvent: atomic unit of traceability
# - SpeciesSustainabilityProfile: per-species sustainability data
# - FisherImpactProfile: socioeconomic fisher metrics
# - TraceabilityChain: full catch-to-buyer linkage
# - ComplianceDocument: flexible export document registry

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class CatchMethod(str, enum.Enum):
    HANDLINE         = "handline"
    LONGLINE         = "longline"
    TRAP             = "trap"
    GILLNET          = "gillnet"
    PURSE_SEINE      = "purse_seine"
    SPEAR            = "spear"
    BEACH_SEINE      = "beach_seine"
    CAST_NET         = "cast_net"
    TRAWL            = "trawl"
    DIVING           = "diving"       # Octopus, sea cucumber
    GLEANING         = "gleaning"     # Shellfish, low tide collection
    OTHER            = "other"


class VesselSizeCategory(str, enum.Enum):
    CANOE            = "canoe"        # Non-motorised, < 5m
    SMALL_MOTORISED  = "small_motorised"  # 5-10m
    MEDIUM           = "medium"       # 10-20m
    LARGE            = "large"        # > 20m
    INDUSTRIAL       = "industrial"   # Commercial vessels


class IUURiskLevel(str, enum.Enum):
    LOW              = "low"          # All permits verified
    MEDIUM           = "medium"       # Some documentation gaps
    HIGH             = "high"         # Significant compliance issues
    FLAGGED          = "flagged"      # Active IUU concern
    UNKNOWN          = "unknown"      # Not yet assessed


class SustainabilityStatus(str, enum.Enum):
    GREEN            = "green"        # Sustainable — recommended
    ORANGE           = "orange"       # Some concerns — use with care
    RED              = "red"          # Avoid — unsustainable
    UNASSESSED       = "unassessed"   # Not yet evaluated


class ComplianceDocType(str, enum.Enum):
    CATCH_CERTIFICATE     = "catch_certificate"
    KEBS_EXPORT           = "kebs_export"
    EU_CATCH_CERTIFICATE  = "eu_catch_certificate"
    HEALTH_CERTIFICATE    = "health_certificate"
    ECO_LABEL             = "eco_label"
    ESG_REPORT            = "esg_report"
    HACCP_RECORD          = "haccp_record"
    FISHER_EARNINGS       = "fisher_earnings"
    IMPACT_REPORT         = "impact_report"


# ── CATCH EVENT ───────────────────────────────────────────────────

class CatchEvent(Base):
    __tablename__ = "catch_events"

    id              = Column(Integer, primary_key=True, index=True)

    # ── LINKAGE ───────────────────────────────────────────────
    lot_id          = Column(Integer, ForeignKey("inventory_lots.id"),
                             nullable=True, index=True)
    # Linked after lot is created — may be null if logged at sea

    fisher_id       = Column(Integer, ForeignKey("users.id"),
                             nullable=False, index=True)

    # ── CATCH IDENTITY ────────────────────────────────────────
    species         = Column(String(100), nullable=False, index=True)
    scientific_name = Column(String(200), nullable=True)
    # e.g. Thunnus albacares for Yellowfin Tuna

    weight_kg       = Column(Float, nullable=False)
    individual_count = Column(Integer, nullable=True)
    # Number of fish — important for size/maturity data

    # ── CATCH METHOD + GEAR ───────────────────────────────────
    catch_method    = Column(
        SAEnum(CatchMethod, name="catchmethod", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    gear_type       = Column(String(100), nullable=True)
    gear_details    = Column(String(200), nullable=True)
    # e.g. "monofilament 0.4mm, 200m depth"

    # ── LOCATION + TIMING ─────────────────────────────────────
    landing_site    = Column(String(100), nullable=False, index=True)
    bmu_reference   = Column(String(100), nullable=True)
    landing_officer = Column(String(100), nullable=True)
    # Name of BMU/KFS officer who verified landing

    catch_timestamp = Column(DateTime(timezone=True), nullable=True)
    # Exact time — critical for night landings and traceability

    landing_timestamp = Column(DateTime(timezone=True), nullable=True)
    # When fish arrived at landing site

    fishing_ground  = Column(String(200), nullable=True)
    # e.g. "Pemba Channel", "Wasini Island area", "offshore 40nm"

    gps_lat_catch   = Column(Float, nullable=True)
    gps_lng_catch   = Column(Float, nullable=True)
    # Where fish was caught — IoT vessel devices will populate this

    # ── VESSEL ────────────────────────────────────────────────
    vessel_reg      = Column(String(50), nullable=True, index=True)
    vessel_name     = Column(String(100), nullable=True)
    vessel_size_category = Column(
        SAEnum(VesselSizeCategory, name="vesselsizecategory", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    crew_size       = Column(Integer, nullable=True)
    # Total crew on the fishing trip

    trip_duration_days = Column(Float, nullable=True)
    # How many days was the trip? Important for deep-sea data

    # ── CREW COMPOSITION ──────────────────────────────────────
    female_crew_count = Column(Integer, nullable=True)
    # Gender participation — important for ESG and grants

    # ── PERMITS + COMPLIANCE ──────────────────────────────────
    fishing_permit_no   = Column(String(100), nullable=True)
    permit_expiry_date  = Column(String(20), nullable=True)
    is_cross_border     = Column(Boolean, default=False, nullable=True)
    # True for Tanzanian/Pemba fishers operating in Kenyan waters

    origin_country      = Column(String(50), default="KE", nullable=True)
    # KE, TZ, MZ etc.

    iuu_risk_level      = Column(
        SAEnum(IUURiskLevel, name="iuurisklevel", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=IUURiskLevel.UNKNOWN,
        nullable=True
    )
    iuu_risk_notes      = Column(Text, nullable=True)

    # ── CONDITION AT LANDING ──────────────────────────────────
    temperature_at_landing_celsius = Column(Float, nullable=True)
    # Fish temperature when landed — food safety record

    ice_used            = Column(Boolean, nullable=True)
    ice_kg              = Column(Float, nullable=True)
    # Ice-to-fish ratio matters for quality

    condition_notes     = Column(Text, nullable=True)

    # ── VERIFIED BY ───────────────────────────────────────────
    verified_by         = Column(String(100), nullable=True)
    # MarineCatch staff or BMU officer who verified

    verification_method = Column(String(100), nullable=True)
    # "visual", "permit_check", "bmu_record", "digital"

    # ── METADATA ──────────────────────────────────────────────
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True),
                                 server_default=func.now())
    updated_at          = Column(DateTime(timezone=True),
                                 onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    fisher  = relationship("User", foreign_keys=[fisher_id])
    lot     = relationship("InventoryLot", foreign_keys=[lot_id])

    def __repr__(self):
        return (
            f"<CatchEvent {self.species} {self.weight_kg}kg "
            f"by fisher={self.fisher_id} at {self.landing_site}>"
        )


# ── SPECIES SUSTAINABILITY PROFILE ────────────────────────────────

class SpeciesSustainabilityProfile(Base):
    __tablename__ = "species_sustainability_profiles"

    id              = Column(Integer, primary_key=True, index=True)
    species_name    = Column(String(100), unique=True, nullable=False, index=True)
    scientific_name = Column(String(200), nullable=True)
    local_names     = Column(String(300), nullable=True)
    # Swahili, local dialect names: "Jodari, Kijodari"

    # ── SUSTAINABILITY ────────────────────────────────────────
    sustainability_status = Column(
        SAEnum(SustainabilityStatus, name="sustainabilitystatus", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        default=SustainabilityStatus.UNASSESSED,
        nullable=False
    )
    sassi_rating        = Column(String(20), nullable=True)
    # SASSI (Southern African Sustainable Seafood Initiative) rating

    iucn_status         = Column(String(50), nullable=True)
    # IUCN Red List status

    # ── FISHING RESTRICTIONS ──────────────────────────────────
    minimum_size_cm     = Column(Float, nullable=True)
    # Legal minimum landing size

    closed_season_start = Column(String(20), nullable=True)
    closed_season_end   = Column(String(20), nullable=True)
    # Breeding season restrictions

    permitted_gear      = Column(String(300), nullable=True)
    # Comma-separated: "handline,longline,trap"

    prohibited_gear     = Column(String(300), nullable=True)
    # "trawl,beach_seine" in some areas

    export_permitted    = Column(Boolean, default=True, nullable=True)
    requires_permit     = Column(Boolean, default=False, nullable=True)

    # ── HABITAT ───────────────────────────────────────────────
    habitat             = Column(String(200), nullable=True)
    # "reef, pelagic, demersal, inshore"

    depth_range_m       = Column(String(50), nullable=True)
    # "0-200m"

    # ── MARKET ────────────────────────────────────────────────
    typical_price_range_kes = Column(String(50), nullable=True)
    # "600-900 per kg"

    premium_markets     = Column(String(300), nullable=True)
    # "export, hotels, processors"

    notes               = Column(Text, nullable=True)
    last_reviewed_at    = Column(DateTime(timezone=True), nullable=True)
    created_at          = Column(DateTime(timezone=True),
                                 server_default=func.now())

    def __repr__(self):
        return f"<SpeciesSustainabilityProfile {self.species_name} — {self.sustainability_status}>"


# ── FISHER IMPACT PROFILE ─────────────────────────────────────────

class FisherImpactProfile(Base):
    __tablename__ = "fisher_impact_profiles"

    id              = Column(Integer, primary_key=True, index=True)
    fisher_id       = Column(Integer, ForeignKey("users.id"),
                             unique=True, nullable=False, index=True)

    # ── SOCIOECONOMIC ─────────────────────────────────────────
    household_size      = Column(Integer, nullable=True)
    dependents_count    = Column(Integer, nullable=True)
    primary_income_source = Column(String(100), nullable=True)
    # "fishing", "fishing+farming", "fishing+trading"

    years_fishing       = Column(Integer, nullable=True)
    education_level     = Column(String(50), nullable=True)

    # ── COOPERATIVE + BMU ─────────────────────────────────────
    bmu_name            = Column(String(100), nullable=True)
    bmu_membership_active = Column(Boolean, default=False, nullable=True)
    cooperative_name    = Column(String(100), nullable=True)
    cooperative_member  = Column(Boolean, default=False, nullable=True)

    # ── EQUIPMENT ─────────────────────────────────────────────
    owns_vessel         = Column(Boolean, default=False, nullable=True)
    vessel_count        = Column(Integer, nullable=True)
    has_cold_storage    = Column(Boolean, default=False, nullable=True)
    has_smartphone      = Column(Boolean, default=False, nullable=True)
    # Digital access — important for WhatsApp/USSD channel design

    # ── IMPACT METRICS (computed from transaction history) ────
    # These are updated periodically from order/payout data
    lifetime_catch_kg       = Column(Float, default=0.0, nullable=True)
    lifetime_earnings_kes   = Column(Float, default=0.0, nullable=True)
    total_transactions      = Column(Integer, default=0, nullable=True)
    avg_monthly_earnings_kes = Column(Float, nullable=True)
    last_transaction_at     = Column(DateTime(timezone=True), nullable=True)

    # ── SPECIES PROFILE ───────────────────────────────────────
    primary_species     = Column(String(200), nullable=True)
    # Comma-separated: "tuna,octopus,prawns"

    # ── SAFETY ────────────────────────────────────────────────
    has_life_jacket     = Column(Boolean, nullable=True)
    has_safety_training = Column(Boolean, nullable=True)
    emergency_contact   = Column(String(100), nullable=True)
    # Future: safety-at-sea integration

    # ── METADATA ──────────────────────────────────────────────
    profile_complete    = Column(Boolean, default=False, nullable=False)
    last_updated_at     = Column(DateTime(timezone=True), nullable=True)
    created_at          = Column(DateTime(timezone=True),
                                 server_default=func.now())

    fisher = relationship("User", foreign_keys=[fisher_id])

    def __repr__(self):
        return f"<FisherImpactProfile fisher_id={self.fisher_id}>"


# ── TRACEABILITY CHAIN ────────────────────────────────────────────

class TraceabilityChain(Base):
    __tablename__ = "traceability_chains"

    id              = Column(Integer, primary_key=True, index=True)
    chain_reference = Column(String(50), unique=True, nullable=False, index=True)
    # Format: MC-TRACE-YYYYMMDD-XXXXX

    order_id        = Column(Integer, ForeignKey("orders.id"),
                             nullable=False, index=True)
    lot_id          = Column(Integer, ForeignKey("inventory_lots.id"),
                             nullable=True)
    catch_event_id  = Column(Integer, ForeignKey("catch_events.id"),
                             nullable=True)
    shipment_id     = Column(Integer, ForeignKey("shipments.id"),
                             nullable=True)

    # ── CHAIN SUMMARY ─────────────────────────────────────────
    fisher_name     = Column(String(100), nullable=True)
    fisher_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    landing_site    = Column(String(100), nullable=True)
    catch_date      = Column(String(20), nullable=True)
    species         = Column(String(100), nullable=True)
    quantity_kg     = Column(Float, nullable=True)
    buyer_name      = Column(String(100), nullable=True)
    delivery_date   = Column(String(20), nullable=True)

    # ── COMPLIANCE FLAGS ──────────────────────────────────────
    iuu_risk_level  = Column(String(20), nullable=True)
    cold_chain_maintained = Column(Boolean, nullable=True)
    permits_verified = Column(Boolean, nullable=True)
    bmu_verified    = Column(Boolean, nullable=True)

    # ── EXPORT READINESS ──────────────────────────────────────
    export_ready    = Column(Boolean, default=False, nullable=True)
    export_issues   = Column(Text, nullable=True)
    # Comma-separated issues: "missing_permit,cold_chain_breach"

    generated_at    = Column(DateTime(timezone=True),
                             server_default=func.now())
    updated_at      = Column(DateTime(timezone=True),
                             onupdate=func.now())

    # ── RELATIONSHIPS ─────────────────────────────────────────
    order       = relationship("Order", foreign_keys=[order_id])
    lot         = relationship("InventoryLot", foreign_keys=[lot_id])
    catch_event = relationship("CatchEvent", foreign_keys=[catch_event_id])
    shipment    = relationship("Shipment", foreign_keys=[shipment_id])
    fisher      = relationship("User", foreign_keys=[fisher_id])

    def __repr__(self):
        return f"<TraceabilityChain {self.chain_reference} order={self.order_id}>"


# ── COMPLIANCE DOCUMENT ───────────────────────────────────────────

class ComplianceDocument(Base):
    __tablename__ = "compliance_documents"

    id              = Column(Integer, primary_key=True, index=True)
    doc_reference   = Column(String(50), unique=True, nullable=False, index=True)
    # Format: MC-COMP-YYYYMMDD-XXXXX

    doc_type        = Column(
        SAEnum(ComplianceDocType, name="compliancedoctype", create_type=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    order_id        = Column(Integer, ForeignKey("orders.id"), nullable=True)
    lot_id          = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)
    chain_id        = Column(Integer, ForeignKey("traceability_chains.id"), nullable=True)
    fisher_id       = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ── DOCUMENT CONTENT ──────────────────────────────────────
    content_json    = Column(Text, nullable=True)
    # Full document data as JSON string
    # Different structure per doc_type

    status          = Column(String(20), default="draft", nullable=False)
    # draft, issued, verified, expired, revoked

    issued_by       = Column(String(100), nullable=True)
    issued_at       = Column(DateTime(timezone=True), nullable=True)
    expires_at      = Column(DateTime(timezone=True), nullable=True)
    verified_by     = Column(String(100), nullable=True)
    verified_at     = Column(DateTime(timezone=True), nullable=True)

    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True),
                             server_default=func.now())

    order   = relationship("Order", foreign_keys=[order_id])
    lot     = relationship("InventoryLot", foreign_keys=[lot_id])
    chain   = relationship("TraceabilityChain", foreign_keys=[chain_id])
    fisher  = relationship("User", foreign_keys=[fisher_id])

    def __repr__(self):
        return f"<ComplianceDocument {self.doc_reference} type={self.doc_type}>"