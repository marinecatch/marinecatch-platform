# scripts/seed_dar_es_salaam_geography.py
#
# Dar es Salaam Region, Tanzania — Phase 1 seed. Closed-world
# package. Features not seen in prior regions: standalone FishMarket
# entities distinct from landing sites, a versioned/conflicting
# marine reserve system (DMRS), research institutions, a commercial
# port, and an explicit "informal landing network" observation for
# Kigamboni that deliberately avoids inferring landing-site
# infrastructure from fishing-community presence.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.fisheries_observation import FisheriesObservation
from app.models.intelligence.infrastructure import InfrastructureAsset
from app.models.intelligence.comanagement import MarineManagementArea
from app.models.intelligence.management_area import ManagementArea

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, tier=1):
    existing = db.query(GeographySource).filter(GeographySource.title == title).first()
    if existing:
        return existing
    s = GeographySource(title=title, issuing_organization=org, publication_year=year, reliability_tier=tier)
    db.add(s)
    db.flush()
    return s


def get_or_create_admin(country_code, gtype, name, parent_id=None, source_name=None):
    existing = db.query(AdminGeography).filter(
        AdminGeography.official_name == name, AdminGeography.geography_type == gtype
    ).first()
    if existing:
        return existing
    a = AdminGeography(country_code=country_code, geography_type=gtype, official_name=name,
                        parent_id=parent_id, source_name=source_name, verification_status="OFFICIAL_UNVERIFIED")
    db.add(a)
    db.flush()
    return a


def get_or_create_site(name, district_id=None, site_type="landing_site", confidence="B",
                        source_name=None, verified=False, lat=None, lng=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    conf_score = {"A": 4, "B": 3, "C": 2, "D": 1}.get(confidence, 2)
    s = FishLandingSite(
        official_name=name, county_id=district_id, site_type=site_type,
        latitude=lat, longitude=lng, confidence_score=conf_score,
        verification_status="VERIFIED_OFFICIAL" if verified else "RESEARCH_SOURCE",
        data_verification_stage="field_verified" if verified else "survey_identified",
        source_name=source_name, production_system="wild_capture",
    )
    db.add(s)
    db.flush()
    return s


def add_obs(admin_id, metric_type, value, currency=None, year=None, subtype=None,
            canonical="false", source_name=None):
    o = FisheriesObservation(
        admin_geography_id=admin_id, metric_type=metric_type, metric_subtype=subtype,
        value=value, currency=currency, period_year=year, is_canonical=canonical,
        source_name=source_name, verification_status="VERIFIED_OFFICIAL",
    )
    db.add(o)
    return o


print("=" * 60)
print("SEEDING DAR ES SALAAM REGION, TANZANIA — PHASE 1")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_mlf2020  = get_or_create_source("Annual Fisheries Statistics Report January-December 2020", "Ministry of Livestock and Fisheries", 2020, tier=1)
src_kivukoni = get_or_create_source("Kivukoni Fish Market operational documentation", tier=2)
src_dmrs_gmp = get_or_create_source("Dar es Salaam Marine Reserves System General Management Plan", "Marine Parks and Reserves Tanzania", tier=1)
src_dmrs_cur = get_or_create_source("Dar es Salaam Marine Reserves System (current designation list)", tier=2)
src_tafiri   = get_or_create_source("TAFIRI/NMRC/UDSM fisheries research institution records", tier=2)
src_tanfish  = get_or_create_source("TanFishMarket digital platform launch documentation (Feb 2026)", year=2026, tier=2)
src_port     = get_or_create_source("Dar es Salaam Port commercial/import-export documentation", tier=1)
src_seasense = get_or_create_source("Sea Sense coastal survey — Dar es Salaam landing/market locations", tier=2)
src_comgmt   = get_or_create_source("Fisheries co-management assessment — Kigamboni informal landing points", tier=2)
src_wiomsa   = get_or_create_source("WIOMSA seagrass/ecosystem and billfish research network — DSM sites", tier=2)

print("Sources seeded: 10")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
dsm = get_or_create_admin("TZA", "region", "Dar es Salaam", source_name=src_mlf2020.title)
districts = {
    "Ilala":      get_or_create_admin("TZA", "municipal_council", "Ilala", parent_id=dsm.id),
    "Kinondoni":  get_or_create_admin("TZA", "municipal_council", "Kinondoni", parent_id=dsm.id),
    "Temeke":     get_or_create_admin("TZA", "municipal_council", "Temeke", parent_id=dsm.id),
    "Kigamboni":  get_or_create_admin("TZA", "municipal_council", "Kigamboni", parent_id=dsm.id),
    "Ubungo":     get_or_create_admin("TZA", "municipal_council", "Ubungo", parent_id=dsm.id),
}
print(f"Admin geography: Dar es Salaam > {len(districts)} municipal councils")
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Ubungo"].id,
    claim_field="coastal_scope_rule",
    claim_value="Ubungo is an inland/non-coastal municipal council — seeded for admin completeness, no FishLandingSite records expected.",
    source_id=src_mlf2020.id, is_canonical="false",
))

# ── FISHERIES FRAME ───────────────────────────────────────────────
add_obs(dsm.id, "landing_site_count", 31, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(dsm.id, "fisher_count", 8792, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(dsm.id, "vessel_count", 1240, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(dsm.id, "catch_tonnes", 23110.4, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(dsm.id, "production_value", 108619000000, currency="TZS", year=2020, canonical="true", source_name=src_mlf2020.title)
print("Regional frame seeded: 31 sites, 8,792 fishers, 1,240 vessels, 23,110.4 MT, TZS 108.619bn")

# ── KINONDONI — 6 named BMU/community locations, precise site_type ──
kunduchi = get_or_create_site("Kunduchi", district_id=districts["Kinondoni"].id, site_type="landing_site",
                               confidence="A", source_name=src_mlf2020.title, verified=True,
                               lat=-6.6650, lng=39.2150)
ununio   = get_or_create_site("Ununio", district_id=districts["Kinondoni"].id, site_type="fishing_community",
                               confidence="B", source_name=src_seasense.title)
msasani  = get_or_create_site("Msasani", district_id=districts["Kinondoni"].id, site_type="fishing_community",
                               confidence="B", source_name=src_seasense.title)
mbweni   = get_or_create_site("Mbweni", district_id=districts["Kinondoni"].id, site_type="fishing_community",
                               confidence="B", source_name=src_seasense.title)
kawe     = get_or_create_site("Kawe", district_id=districts["Kinondoni"].id, site_type="fishing_community",
                               confidence="C", source_name=src_seasense.title)
maputo   = get_or_create_site("Maputo", district_id=districts["Kinondoni"].id, site_type="fishing_community",
                               confidence="C", source_name=src_seasense.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=mbweni.id,
    claim_field="colocated_market",
    claim_value="Mbweni has a known fish market distinct from landing-site function — modeled separately as InfrastructureAsset below.",
    source_id=src_seasense.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Kinondoni"].id,
    claim_field="bmu_vs_landing_site_count",
    claim_value="Municipal source states six landing sites AND six BMUs for Kinondoni — do not automatically treat Kawe/Maputo as formal landing sites merely because they appear in the BMU list.",
    source_id=src_mlf2020.id, is_canonical="false",
))
print("Kinondoni sites seeded: 6 (Kunduchi=landing_site confirmed+GPS, Ununio/Msasani/Mbweni/Kawe/Maputo=fishing_community)")

# ── TEMEKE/KIGAMBONI SOUTHERN BELT ────────────────────────────────
minazi = get_or_create_site("Minazi Mikinda", site_type="landing_site", confidence="B",
                             source_name=src_wiomsa.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=minazi.id,
    claim_field="district_attribution_ambiguity",
    claim_value="Historical sources differ on district terminology (Kinondoni-era vs Temeke-era boundary descriptions). District assignment NOT invented — relationship preserved as ambiguous rather than forced. Also included in WIOMSA's Dar es Salaam billfish research network.",
    source_id=src_wiomsa.id, is_canonical="false",
))

mjimwema = get_or_create_site("Mjimwema", district_id=districts["Kigamboni"].id, site_type="landing_site",
                               confidence="B", source_name=src_seasense.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=mjimwema.id,
    claim_field="corridor_note",
    claim_value="Dar es Salaam Master Plan identifies the Kivukoni-Mjimwema corridor as an important urban movement corridor — future SupplyCorridor candidate.",
    source_id=src_seasense.id, is_canonical="false",
))

ferry_landing = get_or_create_site("Kigamboni Ferry", district_id=districts["Kigamboni"].id,
                                    site_type="landing_site", confidence="B", source_name=src_seasense.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=ferry_landing.id,
    claim_field="operational_note",
    claim_value="Central Dar es Salaam fish landing point where many fishers land catch. One of two study communities in a 2026 study.",
    source_id=src_seasense.id, is_canonical="false",
))
ferry_market = InfrastructureAsset(
    landing_site_id=ferry_landing.id, asset_type="fish_market",
    source_name=src_seasense.title, verification_status="RESEARCH_SOURCE",
)
db.add(ferry_market)

buyuni = get_or_create_site("Buyuni", district_id=districts["Kigamboni"].id, site_type="fishing_community",
                             confidence="C", source_name=src_wiomsa.title)
kimbiji = get_or_create_site("Kimbiji", district_id=districts["Kigamboni"].id, site_type="fishing_community",
                              confidence="C", source_name=src_wiomsa.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=kimbiji.id,
    claim_field="ecological_note",
    claim_value="Indian Ocean-facing ward/community; Sea Sense identifies Kimbiji as an important marine turtle nesting area in the Dar es Salaam/Temeke area. Also a seagrass study site.",
    source_id=src_seasense.id, is_canonical="false",
))
puna = get_or_create_site("Puna", district_id=districts["Kigamboni"].id, site_type="fishing_community",
                           confidence="C", source_name=src_wiomsa.title)
mtoni = get_or_create_site("Mtoni Kijichi", district_id=districts["Temeke"].id, site_type="fishing_community",
                            confidence="C", source_name=src_wiomsa.title)
print("Southern belt (Temeke/Kigamboni) sites seeded: Minazi Mikinda, Mjimwema, Kigamboni Ferry (+market), Buyuni, Kimbiji, Puna, Mtoni Kijichi")

# ── KIGAMBONI INFORMAL LANDING NETWORK — deliberately NOT one site ──
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Kigamboni"].id,
    claim_field="landing_infrastructure_coverage",
    claim_value="A substantial portion of Kigamboni fisheries activity has historically used informal/unstructured beach landing points — fishers selling directly from boats or on sandy beaches. Implications: official landing-site counts may underrepresent operational landing points; catch-data coverage may be incomplete; landing-site infrastructure must not be inferred from fishing-community presence alone.",
    source_id=src_comgmt.id, is_canonical="false",
))
print("Kigamboni informal landing network recorded as a coverage-gap observation, not modeled as a single site")

# ── KIVUKONI FISH MARKET — major standalone market, not a landing site ──
kivukoni = InfrastructureAsset(
    asset_type="fish_market", operational_status="OPERATIONAL",
    source_name=src_kivukoni.title, verification_status="VERIFIED_SECONDARY",
)
db.add(kivukoni)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=kivukoni.id,
    claim_field="throughput",
    claim_value="~400 MT/month local wild-capture landings reported; ~350 MT/month additional incoming supply from other sources (imported, inter-regional, aquaculture, unknown origin — not individually broken down). ~13,000 visitors/day. Major urban fish market, central Dar es Salaam.",
    source_id=src_kivukoni.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=kivukoni.id,
    claim_field="origin_classification_framework",
    claim_value="Source package proposes a product-origin taxonomy for market supply: LOCAL_WILDCAPTURE | IMPORTED | INCOMING_FROM_OTHER_TANZANIA_REGION | AQUACULTURE | UNKNOWN_ORIGIN. Not implemented as a schema field in this geography-layer pass — flagged as a strong candidate for the future InventoryLot/operational layer, not built here to avoid scope creep into transactional architecture.",
    source_id=src_kivukoni.id, is_canonical="false",
))
print("Kivukoni Fish Market seeded: ~400 MT/month local + ~350 MT/month incoming, ~13,000 visitors/day (origin taxonomy noted, not modeled as new schema)")

# ── TANFISHMARKET — digital platform, noted not modeled ─────────────
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=dsm.id,
    claim_field="digital_market_platform",
    claim_value="TanFishMarket digital platform launched Feb 2026 (Government-linked). Recorded as a market-context note, not built as a new DigitalMarketPlatform entity — single-instance, low priority for schema investment at this phase.",
    source_id=src_tanfish.id, is_canonical="false",
))

# ── DMRS — Dar es Salaam Marine Reserves System ──────────────────────
dmrs = db.query(MarineManagementArea).filter(MarineManagementArea.designation == "Dar es Salaam Marine Reserves System").first()
if not dmrs:
    dmrs = MarineManagementArea(
        designation="Dar es Salaam Marine Reserves System", source_name=src_dmrs_gmp.title,
        verification_status="VERIFIED_OFFICIAL",
    )
    db.add(dmrs)
    db.flush()

gmp_islands = ["Bongoyo", "Mbudya", "Fungu Yasini", "Pangavini"]
current_islands = ["Bongoyo", "Mbudya", "Fungu Yasini"]  # Pangavini status disputed/absent in current source
for name in gmp_islands:
    existing = db.query(ManagementArea).filter(ManagementArea.name == name).first()
    if not existing:
        db.add(ManagementArea(
            name=name, marine_management_area_id=dmrs.id,
            source_name=src_dmrs_gmp.title, verification_status="RESEARCH_SOURCE",
        ))
db.flush()
db.add(GeographySourceClaim(
    entity_type="marine_management_area", entity_id=dmrs.id,
    claim_field="component_list_conflict",
    claim_value="General Management Plan lists 4 component islands (Bongoyo, Mbudya, Fungu Yasini, Pangavini). A current-designation source lists only 3 (Bongoyo, Mbudya, Fungu Yasini) — Pangavini's current status is not reconciled. Both lists preserved via the 4 seeded ManagementArea rows plus this claim.",
    source_id=src_dmrs_cur.id, is_canonical="false",
))
print("DMRS seeded: 4 component islands (Pangavini's current-status discrepancy flagged, not resolved)")

# ── RESEARCH INSTITUTIONS ────────────────────────────────────────────
institutions = [
    ("TAFIRI (Tanzania Fisheries Research Institute)", "fisheries_research_institution"),
    ("NMRC (Nyegezi Marine Research Centre or equivalent DSM unit)", "fisheries_research_institution"),
    ("UDSM Fisheries/Marine Science Unit", "university_fisheries_unit"),
]
inst_count = 0
for name, atype in institutions:
    existing = db.query(InfrastructureAsset).filter(
        InfrastructureAsset.asset_type == atype, InfrastructureAsset.operator == name
    ).first()
    if not existing:
        db.add(InfrastructureAsset(
            asset_type=atype, operator=name, operational_status="OPERATIONAL",
            source_name=src_tafiri.title, verification_status="VERIFIED_SECONDARY",
        ))
        inst_count += 1
db.flush()
print(f"Research institutions seeded: {inst_count}")

# ── DAR ES SALAAM PORT — commercial, not a fishing landing site ─────
port = InfrastructureAsset(
    asset_type="commercial_port", operational_status="OPERATIONAL",
    source_name=src_port.title, verification_status="VERIFIED_OFFICIAL",
)
db.add(port)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=port.id,
    claim_field="relevance_note",
    claim_value="Dar es Salaam Port — primary commercial import/export gateway for Tanzania mainland. Relevant to seafood trade logistics (import/export flows) but is NOT a fisheries landing site and should not be conflated with the 31-site artisanal landing frame.",
    source_id=src_port.id, is_canonical="false",
))
print("Dar es Salaam Port seeded as commercial_port (explicitly distinct from fisheries landing frame)")

db.commit()

print()
print("=" * 60)
print("DAR ES SALAAM REGION SEEDING COMPLETE")
print("=" * 60)
print("AdminGeography: 1 region + 5 municipal councils")
print("FishLandingSites: ~14 (Kinondoni 6, southern belt 7, Minazi Mikinda 1)")
print(f"InfrastructureAssets: {1 + 1 + inst_count + 1} (Kivukoni market, Ferry market, {inst_count} research institutions, Port)")
print("MarineManagementArea: DMRS, 4 ManagementArea components (conflict flagged)")
print("Data quality flags preserved: Kigamboni informal-landing coverage gap, Kinondoni BMU-vs-landing-site distinction, DMRS island-list conflict, origin-taxonomy noted-not-built")

db.close()