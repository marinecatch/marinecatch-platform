# scripts/seed_lindi_geography.py
#
# Lindi Region, Tanzania — Phase 1 seed. Closed-world package.
# Key discipline: 29 Kilwa BMUs explicitly NOT treated as 29
# landing sites (BMU -> FishingCommunity/FisheriesManagementUnit,
# not BMU=LandingSite). Songosongo gas infrastructure deliberately
# excluded as out-of-scope. Protected-species interaction
# (Zanzibar guitarfish) recorded as field observation, not a
# target fishery.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.fisheries_observation import FisheriesObservation
from app.models.intelligence.infrastructure import InfrastructureAsset
from app.models.fisheries_data import Species

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
                        verification="RESEARCH_SOURCE", source_name=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    conf_score = {"A": 4, "B": 3, "C": 2, "D": 1}.get(confidence, 2)
    s = FishLandingSite(
        official_name=name, county_id=district_id, site_type=site_type,
        confidence_score=conf_score, verification_status=verification,
        data_verification_stage="field_verified" if verification == "VERIFIED_OFFICIAL" else "survey_identified",
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
print("SEEDING LINDI REGION, TANZANIA — PHASE 1")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_mlf2020   = get_or_create_source("Annual Fisheries Statistics Report January-December 2020", "Ministry of Livestock and Fisheries", 2020, tier=1)
src_seaweed_bmu = get_or_create_source("Tanzania Ministry of Livestock and Fisheries 2023/2024 seaweed-farming groups/BMU listing", "Ministry of Livestock and Fisheries", 2023, tier=1)
src_tasfam    = get_or_create_source("TASFAM site assessments (fish landing, coordination centre, seaweed warehouse projects)", year=2026, tier=1)
src_port      = get_or_create_source("Kilwa Masoko Fishing Port project documentation", tier=1)
src_tafiri_som = get_or_create_source("TAFIRI-linked field research — Somanga guitarfish observation", year=2025, tier=1)
src_bmu2017   = get_or_create_source("2017 BMU report — Somanga registered fishers", year=2017, tier=2)
src_lindi_mdp = get_or_create_source("Lindi Municipal development plan", tier=1)
src_coast     = get_or_create_source("State of the Coast landing-site map", tier=2)

print("Sources seeded: 8")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
lindi = get_or_create_admin("TZA", "region", "Lindi", source_name=src_mlf2020.title)
districts = {
    "Kilwa":          get_or_create_admin("TZA", "district_council", "Kilwa", parent_id=lindi.id),
    "Lindi Municipal": get_or_create_admin("TZA", "municipal_council", "Lindi Municipal", parent_id=lindi.id),
}
print(f"Admin geography: Lindi > {len(districts)} coastal fisheries districts")

# ── FISHERIES FRAME ───────────────────────────────────────────────
add_obs(lindi.id, "landing_site_count", None, year=2020, canonical="false", source_name=src_mlf2020.title,
        subtype="count_not_independently_confirmed_in_this_pass")
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=lindi.id,
    claim_field="named_site_register_completeness",
    claim_value="Regional landing-site frame count not independently re-verified in this script pass. BMU listing provides 10+29 named Kilwa BMU-associated locations (see below); these are explicitly NOT a 1:1 landing-site count.",
    source_id=src_mlf2020.id, is_canonical="false",
))

# ── KILWA MASOKO FISHING PORT — major infrastructure, near-completion ──
masoko = get_or_create_site("Kilwa Masoko", district_id=districts["Kilwa"].id, site_type="landing_site",
                             confidence="A", verification="VERIFIED_OFFICIAL", source_name=src_port.title)
port = InfrastructureAsset(
    landing_site_id=masoko.id, asset_type="fishing_port",
    operational_status="NEAR_COMPLETION", funding_program="National fisheries infrastructure programme",
    reported_value=280000000000, reported_value_currency="TZS",
    source_name=src_port.title, verification_status="VERIFIED_OFFICIAL",
)
db.add(port)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=port.id,
    claim_field="implementation_status",
    claim_value="TZS 280 billion project, reported 98.9% complete. Includes: ice plant (100 tonnes/day capacity), cold storage, planned fish-meal factory. Status explicitly NOT marked OPERATIONAL — NEAR_COMPLETION/COMMISSIONING phase per source.",
    source_id=src_port.id, is_canonical="false",
))
print("Kilwa Masoko Fishing Port seeded: TZS 280bn, 98.9% complete, ice plant 100t/day, cold storage, planned fish-meal factory")

# ── DRYING RACKS — explicitly NOT 40 facilities ─────────────────────
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=masoko.id,
    claim_field="equipment_handover",
    claim_value="40 fish-drying racks handed over, value TZS 117,000,000, target fishery: sardine/small pelagic, handover year 2025, status IMPLEMENTED. Do NOT interpret as 40 separate processing facilities — this is equipment count, not facility count.",
    source_id=src_tasfam.id, is_canonical="false",
))

# ── KILWA KIVINJE ─────────────────────────────────────────────────
kivinje = get_or_create_site("Kilwa Kivinje", district_id=districts["Kilwa"].id, site_type="landing_site",
                              confidence="B", verification="RESEARCH_SOURCE", source_name=src_tasfam.title)
kivinje_project = InfrastructureAsset(
    landing_site_id=kivinje.id, asset_type="landing_site_development_project",
    operational_status="PLANNED_SITE_ASSESSED",
    source_name=src_tasfam.title, verification_status="RESEARCH_SOURCE",
)
db.add(kivinje_project)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=kivinje_project.id,
    claim_field="scope",
    claim_value="TASFAM March 2026 assessment identified Kilwa Kivinje for a fish landing site and coordination centre. This is a development/upgrade project and does NOT replace the existing Kilwa Kivinje landing-site record. Sardine/small-pelagic fishery with drying-storage-wholesale value chain. Species left at SPECIES_GROUP=SARDINE/SMALL_PELAGIC level — no specific binomial assigned without taxonomic evidence.",
    source_id=src_tasfam.id, is_canonical="false",
))
print("Kilwa Kivinje seeded: landing site + separate development project (project does not replace existing record)")

# ── SOMANGA — strong fisheries evidence + protected species ─────────
somanga_site = get_or_create_site("Somanga", district_id=districts["Kilwa"].id, site_type="landing_site",
                                   confidence="A", verification="VERIFIED_OFFICIAL", source_name=src_tafiri_som.title)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=somanga_site.id,
    claim_field="registered_fishers",
    claim_value="920 registered fishers (2017 BMU report, Somanga BMU scope). Historical reference only — not current population.",
    source_id=src_bmu2017.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=somanga_site.id,
    claim_field="ecological_setting",
    claim_value="Associated with mangrove, sheltered bay, small-scale fishing, community fisheries monitoring. Boats land in a small bay sheltered by mangrove. Relationship chain: Somanga -> Mangrove -> Coastal fishing -> Landing site -> BMU.",
    source_id=src_tafiri_som.id, is_canonical="false",
))

guitarfish = db.query(Species).filter(Species.common_name == "Zanzibar Guitarfish").first()
if not guitarfish:
    guitarfish = Species(
        common_name="Zanzibar Guitarfish", scientific_name="Acroteriobatus zanzibarensis",
        family="Rhinobatidae", category="other",
        source_name=src_tafiri_som.title, verification_status="VERIFIED_OFFICIAL", iuu_risk_flag=True,
        notes="Protected/sensitive species interaction recorded at Somanga, not a target fishery.",
    )
    db.add(guitarfish)
    db.flush()
db.add(GeographySourceClaim(
    entity_type="species", entity_id=guitarfish.id,
    claim_field="landing_observation",
    claim_value="56 individuals observed landed at Somanga, period June-September 2025, TAFIRI-linked field research. This is a field observation count, NOT a stock abundance estimate.",
    source_id=src_tafiri_som.id, is_canonical="false",
))
print("Somanga seeded: landing site + 920-fisher 2017 baseline (non-current) + Zanzibar guitarfish field observation (56 individuals, not a target fishery)")

# ── SONGOSONGO — multi-sector, energy explicitly excluded ────────────
songosongo = get_or_create_site("Songosongo", district_id=districts["Kilwa"].id, site_type="fishing_community",
                                 confidence="B", source_name=src_tasfam.title)
seaweed_wh = InfrastructureAsset(
    landing_site_id=songosongo.id, asset_type="seaweed_storage_facility",
    operational_status="PLANNED_SITE_ASSESSED",
    source_name=src_tasfam.title, verification_status="RESEARCH_SOURCE",
)
db.add(seaweed_wh)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=seaweed_wh.id,
    claim_field="status_note",
    claim_value="2026 TASFAM site assessment identified Songosongo for a seaweed storage warehouse. Do NOT assume construction is complete.",
    source_id=src_tasfam.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=songosongo.id,
    claim_field="scope_exclusion",
    claim_value="Songosongo has multiple sector connections: fisheries, seaweed, marine resources, natural gas, coastal infrastructure. It must NOT be represented only as an energy location. However, gas wells/processing infrastructure (transported toward Somanga/Kinyerezi) are DELIBERATELY EXCLUDED from this fisheries geography layer — EnergyInfrastructure/GasField/GasProcessingFacility/PipelineCorridor are explicitly out of scope. Logistics relationship (marine transport <-> coastal roads <-> fisheries communities) may be modeled later where evidence supports it.",
    source_id=src_tasfam.id, is_canonical="false",
))
print("Songosongo seeded: fishing_community + seaweed warehouse project; gas infrastructure explicitly excluded (out of scope)")

# ── SONGO MNARA & KILWA KISIWANI — historical, NOT auto-classified ──
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Kilwa"].id,
    claim_field="historical_sites_not_seeded_as_landing_sites",
    claim_value="Songo Mnara (coastal island/historical site) and Kilwa Kisiwani (major historical/cultural marine landscape, historic port) appear in the State of the Coast landing-site map but are deliberately NOT auto-classified as fishing landing sites. Kilwa Kisiwani's historic port function must not be merged with the modern Kilwa Masoko fishing port. Seed only where a fisheries-specific source supports it — not seeded as FishLandingSite records in this pass.",
    source_id=src_coast.id, is_canonical="false",
))
print("Songo Mnara and Kilwa Kisiwani: recorded as historical/cultural claim only, NOT seeded as landing sites")

# ── SOUTHERN KILWA BMU-ASSOCIATED LOCATIONS — BMU != LandingSite ────
kilwa_bmu_names = [
    "Somanga Kusini", "Somanga Kaskazini", "Nyamatungutungu", "Malalani",
    "Kisongo", "Rushungi", "Kiswere", "Namakongoro", "Masoko", "Mtoni",
]
bmu_site_count = 0
for name in kilwa_bmu_names:
    get_or_create_site(name, district_id=districts["Kilwa"].id, site_type="fishing_community",
                        confidence="C", verification="RESEARCH_SOURCE", source_name=src_seaweed_bmu.title)
    bmu_site_count += 1
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Kilwa"].id,
    claim_field="bmu_vs_landing_site_discipline",
    claim_value=f"10 southern Kilwa BMU-associated locations seeded as site_type=fishing_community, NOT landing_site: {', '.join(kilwa_bmu_names)}. Source: Ministry 2023/2024 seaweed-farming groups/BMU listing. Do not assume every BMU is a distinct landing site. Entity relation used: BMU -> FishingCommunity / FisheriesManagementUnit, not BMU=LandingSite.",
    source_id=src_seaweed_bmu.id, is_canonical="false",
))
print(f"Southern Kilwa BMU locations seeded: {bmu_site_count} (all as fishing_community, explicitly not landing_site)")

# ── LINDI MUNICIPAL CLUSTER ───────────────────────────────────────
lmc_sites = {
    "Mchinga I":  "fishing_community",
    "Mchinga II": "fishing_community",
    "Ruvu":       "fishing_community",
    "Kitumbikwela": "fishing_community",
}
for name, stype in lmc_sites.items():
    get_or_create_site(name, district_id=districts["Lindi Municipal"].id, site_type=stype,
                        confidence="B", source_name=src_lindi_mdp.title)

add_obs(districts["Lindi Municipal"].id, "catch_tonnes", 300, year=2020, canonical="false",
        subtype="municipal_baseline", source_name=src_lindi_mdp.title)
add_obs(districts["Lindi Municipal"].id, "catch_tonnes", 420, year=2024, canonical="false",
        subtype="municipal_target_not_actual", source_name=src_lindi_mdp.title)
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Lindi Municipal"].id,
    claim_field="production_figure_type",
    claim_value="Lindi Municipal development plan reports a 2020 baseline of 300 tonnes with a 2024 TARGET of 420 tonnes. The 420t figure is a planning target, NOT a verified current production figure — seeded as municipal_target_not_actual, not as an achieved statistic. Plan also records coastal patrols against illegal fishing.",
    source_id=src_lindi_mdp.id, is_canonical="false",
))
print(f"Lindi Municipal cluster seeded: {len(lmc_sites)} sites, 300t 2020 baseline + 420t 2024 TARGET (not actual)")

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("LINDI REGION SEEDING COMPLETE")
print("=" * 60)
print("AdminGeography: 1 region + 2 districts (Kilwa, Lindi Municipal)")
print(f"FishLandingSites: Kilwa Masoko, Kilwa Kivinje, Somanga (3 landing_site, verified) + Songosongo + {bmu_site_count} BMU locations + {len(lmc_sites)} Lindi Municipal (fishing_community)")
print("InfrastructureAssets: Kilwa Masoko Port (98.9% complete, TZS 280bn), Kilwa Kivinje dev project, Songosongo seaweed warehouse")
print("Species: Zanzibar Guitarfish (protected-species interaction, not target fishery)")
print("Data quality flags preserved: BMU!=LandingSite discipline (10 Kilwa + implied in 2017 listing), energy infrastructure excluded, historical sites not auto-classified, 420t target not actual")

db.close()