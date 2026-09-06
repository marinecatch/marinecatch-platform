# app/models/__init__.py
# All models imported here so Alembic sees them all.
# Add every new model to this file.

from app.models.user import User
from app.models.cold_storage import ColdStorageFacility
from app.models.inventory_lot import InventoryLot
from app.models.fish import FishListing
from app.models.order import Order
from app.models.payment import PaymentTransaction
from app.models.logistics import DeliveryZone, FulfillmentHub, LogisticsProvider, Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.esg import (
    CatchEvent, SpeciesSustainabilityProfile,
    FisherImpactProfile, TraceabilityChain, ComplianceDocument
)
from app.models.fisher_cluster import FisherCluster
from app.models.organization import Organization
from app.models.fisheries_data import Species, LandingSite, HistoricalLanding
# Geography Intelligence Layer
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.geographic_alias import GeographicAlias
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.fishing_ground import FishingGround
from app.models.intelligence.comanagement import JointCoManagementArea, MarineManagementArea
from app.models.intelligence.infrastructure import InfrastructureAsset, ColdChainAsset
from app.models.intelligence.logistics_graph import LogisticsNode, SupplyCorridor, SupplyCorridorNode
from app.models.intelligence.species_availability import SpeciesAvailability, SpeciesSeasonality
from app.models.intelligence.verification import FieldVerification, SiteCommercialScore, SiteInvestmentScore
from app.models.intelligence.market import Market
from app.models.intelligence.fishing_gear import FishingGear
from app.models.intelligence.ecological_zone import EcologicalZone
from app.models.intelligence.county_landing_baseline import CountyLandingBaseline
from app.models.intelligence.species_habitat_association import SpeciesHabitatAssociation
from app.models.intelligence.species_gear_association import SpeciesGearAssociation
from app.models.intelligence.species_market_price import SpeciesMarketPrice
from app.models.intelligence.species_processing_profile import SpeciesProcessingProfile