# app/models/inventory_lot.py
#
# WHY THIS FILE EXISTS:
# InventoryLot is the backbone of MarineCatch Africa.
# Every piece of seafood in the system — whether listed
# by a fisher, bought by MarineCatch, or reserved for a
# processor — is represented as an InventoryLot.
#
# This single model supports all three business modes:
# Mode 1: Fisher lists catch (ownership=marketplace)
# Mode 2: MarineCatch buys and resells (ownership=marinecatch_owned)
# Mode 3: Reserved for processor/hotel contracts (ownership=contract_reserved)
#
# Real examples:
# LOT-001: Abdalla Masudi, 40kg octopus, Kibuyuni, marketplace
# LOT-002: Bakari Usi, 85kg tuna, Kibuyuni, marketplace
# LOT-003: MarineCatch bought 200kg prawns from Juma Riziki,
#           stored in Ukunda cold storage, selling to Sea Harvest

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ── ENUMS ─────────────────────────────────────────────────────────

class OwnershipType(str, enum.Enum):
    """
    Who owns this inventory and bears the risk.
    This drives accounting, payments, and logistics responsibility.
    """
    MARKETPLACE        = "marketplace"        # Fisher owns, MC facilitates
    MARINECATCH_OWNED  = "marinecatch_owned"  # MC bought it, owns risk+margin
    CONSIGNMENT        = "consignment"        # Fisher left it with us to sell
    CONTRACT_RESERVED  = "contract_reserved"  # Bought for specific buyer contract


class ProductForm(str, enum.Enum):
    """
    How the fish was prepared at landing.
    Fishers do minimal processing — mostly whole or gutted.
    """
    WHOLE_UNGUTTED  = "whole_ungutted"   # Most common from fishers
    WHOLE_GUTTED    = "whole_gutted"     # Basic processing done
    HEADED_GUTTED   = "headed_gutted"    # Head removed + gutted
    FILLET          = "fillet"           # Rare from fishers
    DRIED           = "dried"
    SMOKED          = "smoked"
    LIVE            = "live"             # Oysters, crab, lobster
    OTHER           = "other"


class QualityGrade(str, enum.Enum):
    """
    Grade assigned at inspection.
    A = premium, B = standard, C = discount/processing only.
    Processors like Sea Harvest typically require Grade A only.
    """
    A       = "A"        # Premium — hotels, processors, export
    B       = "B"        # Standard — general market
    C       = "C"        # Below standard — processing/drying only
    PENDING = "pending"  # Not yet inspected


class LotCondition(str, enum.Enum):
    FRESH     = "fresh"
    FROZEN    = "frozen"
    DRIED     = "dried"
    LIVE      = "live"
    PROCESSED = "processed"


class FulfillmentMode(str, enum.Enum):
    """
    How the fish physically moves from seller to buyer.
    MarineCatch starts with outsourced logistics,
    evolves to own fleet on key routes later.
    """
    SELF_PICKUP              = "self_pickup"
    SELLER_DELIVERY          = "seller_delivery"
    THIRD_PARTY_LOGISTICS    = "third_party_logistics"
    MARINECATCH_FULFILLMENT  = "marinecatch_fulfillment"


class LogisticsResponsibility(str, enum.Enum):
    BUYER        = "buyer"
    SELLER       = "seller"
    MARINECATCH  = "marinecatch"
    THIRD_PARTY  = "third_party"


class LotStatus(str, enum.Enum):
    """
    Full lifecycle of an inventory lot.
    Never use boolean is_sold — status covers all states.
    """
    AVAILABLE      = "available"       # Ready to buy
    RESERVED       = "reserved"        # Held for pending order
    PARTIALLY_SOLD = "partially_sold"  # Some kg sold, rest available
    SOLD           = "sold"            # Fully sold
    IN_TRANSIT     = "in_transit"      # Being delivered
    DELIVERED      = "delivered"       # Reached buyer
    COMPLETED      = "completed"       # Transaction fully closed
    EXPIRED        = "expired"         # Past estimated expiry
    SPOILED        = "spoiled"         # Quality failure
    REJECTED       = "rejected"        # Failed QA inspection


# ── MODEL ─────────────────────────────────────────────────────────

class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    # ── IDENTITY ─────────────────────────────────────────────
    id              = Column(Integer, primary_key=True, index=True)
    lot_number      = Column(String(50), unique=True, nullable=False, index=True)
    # e.g. "MC-LOT-20251003-KC001"
    # MC = MarineCatch, KC = Kibuyuni Catch
    # Human readable, printable on labels, scannable later

    traceability_code = Column(String(100), unique=True, nullable=True)
    # Future: QR code reference, blockchain hash
    # Export documentation will reference this

    batch_number    = Column(String(50), nullable=True, index=True)
    # Groups multiple lots from same procurement run
    # e.g. "BATCH-20251003-SHIMONI-001"

    # ── PRODUCT ──────────────────────────────────────────────
    species         = Column(String(50), nullable=False, index=True)
    product_form = Column(
        SAEnum(
            ProductForm,
            name="productform",
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=ProductForm.WHOLE_UNGUTTED,
        nullable=False
    )
    weight_kg       = Column(Float, nullable=False)
    # Original weight at landing — never changes

    available_kg    = Column(Float, nullable=False)
    # Decreases as orders are placed
    # available_kg = weight_kg - reserved_kg - sold_kg

    reserved_kg     = Column(Float, default=0.0, nullable=False)
    # Held for pending/confirmed orders not yet delivered

    grade = Column(
        SAEnum(QualityGrade, name="qualitygrade", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=QualityGrade.PENDING, nullable=False
    )

    condition = Column(
        SAEnum(LotCondition, name="lotcondition", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=LotCondition.FRESH, nullable=False
    )
    notes           = Column(Text, nullable=True)
    # Any special notes about this lot

    # ── SOURCE + TRACEABILITY ─────────────────────────────────
    source_user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    # The fisher or supplier who provided this fish

    source_name     = Column(String(100), nullable=False)
    # Denormalized for quick display — Abdalla Masudi

    landing_site    = Column(String(50), nullable=False, index=True)
    # kibuyuni, shimoni, ukunda, majoreni...

    bmu_reference   = Column(String(100), nullable=True)
    # Beach Management Unit record number
    # Required for export compliance later

    catch_date      = Column(String(20), nullable=True)
    # When fish was caught — "2025-10-03"

    landing_date    = Column(String(20), nullable=True)
    # When fish arrived at landing site

    vessel_name     = Column(String(100), nullable=True)
    vessel_reg      = Column(String(50), nullable=True)
    # Boat registration — BMU record

    # ── OWNERSHIP ─────────────────────────────────────────────
    ownership_type = Column(
        SAEnum(OwnershipType, name="ownershiptype", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=OwnershipType.MARKETPLACE, nullable=False, index=True
    )
    # This single field changes everything:
    # - who bears spoilage risk
    # - how payment flows
    # - what margin MarineCatch earns
    # - how logistics is assigned

    # ── PRICING ───────────────────────────────────────────────
    purchase_price_per_kg = Column(Float, nullable=True)
    # What MarineCatch paid (Mode 2 only)
    # null for marketplace lots (fisher sets their own price)

    selling_price_per_kg  = Column(Float, nullable=False)
    # The asking price buyers see

    min_price_per_kg      = Column(Float, nullable=True)
    # Floor price — won't sell below this
    # Useful for negotiations with processors

    # ── FEES (Revenue Stack) ──────────────────────────────────
    # These are added ON TOP of the fish price
    # This is what transforms marketplace into infrastructure

    cold_storage_fee_per_kg_per_day = Column(Float, default=0.0)
    # Charged if fish stored in MarineCatch cold room
    # e.g. 5 KES/kg/day in Ukunda

    handling_fee_kes      = Column(Float, default=0.0)
    # Loading, unloading, sorting

    qa_fee_kes            = Column(Float, default=0.0)
    # Quality assurance inspection fee

    # ── COLD STORAGE ──────────────────────────────────────────
    cold_storage_id       = Column(
        Integer,
        ForeignKey("cold_storage_facilities.id"),
        nullable=True
    )
    # null = not in cold storage (e.g. same-day marketplace sale)
    # set = stored in Ukunda/Kinondo/Kibuyuni facility

    storage_location      = Column(String(200), nullable=True)
    # "Ukunda Cold Room A, Row 3, Shelf 2"

    storage_entry_date    = Column(DateTime(timezone=True), nullable=True)
    storage_exit_date     = Column(DateTime(timezone=True), nullable=True)

    # ── LOGISTICS ─────────────────────────────────────────────
    fulfillment_mode = Column(
        SAEnum(FulfillmentMode, name="fulfillmentmode", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=FulfillmentMode.SELF_PICKUP, nullable=True
    )
    logistics_responsibility = Column(
        SAEnum(LogisticsResponsibility, name="logisticsresponsibility", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=LogisticsResponsibility.BUYER, nullable=True
    )
    # ── STATUS ─────────
    # ── VISIBILITY ────────────────────────────────────────────
    # Controls who can see this inventory lot.
    # Recommended by Alpha Seafood — commercial confidentiality.
    visibility      = Column(
        String(20),
        default="public",
        nullable=False,
        index=True
    )
    # public        → visible to all buyers on marketplace
    # partner_only  → visible to verified partners only
    # private       → admin and owner only
    # api_shared    → accessible via API with valid key
    lot_status = Column(
        SAEnum(LotStatus, name="lotstatus", create_type=False,
               values_callable=lambda x: [e.value for e in x]),
        default=LotStatus.AVAILABLE, nullable=False, index=True
    )
    is_active       = Column(Boolean, default=True, nullable=False)

    # ESG + sustainability fields
    gear_type            = Column(String(50), nullable=True)
    # "handline", "longline", "trap", "gillnet", "diving"

    iuu_risk_flag        = Column(Boolean, default=False, nullable=False)
    # True if: no BMU record, expired license, or banned species

    sustainability_notes = Column(Text, nullable=True)

    # ── EXPIRY ────────────────────────────────────────────────
    estimated_expiry = Column(DateTime(timezone=True), nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────
    created_at      = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at      = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # ── RELATIONSHIPS ─────────────────────────────────────────
    source_user     = relationship("User", foreign_keys=[source_user_id])
    cold_storage    = relationship("ColdStorageFacility",
                                   foreign_keys=[cold_storage_id])

    def __repr__(self):
        return (
            f"<InventoryLot {self.lot_number} "
            f"species={self.species} "
            f"available={self.available_kg}kg "
            f"status={self.lot_status}>"
        )