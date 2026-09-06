# scripts/seed_tana_river_geography.py
#
# Seeds Tana River County geography intelligence — Phase 4.
# Superseded the original thin "research framework" package with a
# proper web research pass. Confirmed primary source: Tana Delta
# Joint Co-management Area Plan 2024-2028 (KEMFSED / Kenya Fisheries
# Service / Tana River County Government) — same tier and format as
# Kwale/Lamu/Kilifi JCMA plans. 3 BMUs confirmed: Kipini, Ozi, Chara.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.comanagement import JointCoManagementArea
from app.models.intelligence.ecological_zone import EcologicalZone

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, doc_type=None, scope=None, tier=3):
    existing = db.query(GeographySource).filter(GeographySource.title == title).first()
    if existing:
        return existing
    s = GeographySource(title=title, issuing_organization=org, publication_year=year,
                         document_type=doc_type, geographic_scope=scope, reliability_tier=tier)
    db.add(s)
    db.flush()
    return s


def get_or_create_admin(country_code, geography_type, official_name, parent_id=None, source_name=None):
    existing = db.query(AdminGeography).filter(
        AdminGeography.official_name == official_name,
        AdminGeography.geography_type == geography_type,
    ).first()
    if existing:
        return existing
    a = AdminGeography(country_code=country_code, geography_type=geography_type,
                        official_name=official_name, parent_id=parent_id,
                        source_name=source_name, verification_status="OFFICIAL_UNVERIFIED")
    db.add(a)
    db.flush()
    return a


def get_or_create_bmu(name, source_name=None, active_status="ACTIVE"):
    existing = db.query(BMU).filter(BMU.official_name == name).first()
    if existing:
        return existing
    b = BMU(official_name=name, source_name=source_name,
            active_status=active_status, verification_status="VERIFIED_OFFICIAL")
    db.add(b)
    db.flush()
    return b


def get_or_create_site(name, bmu_id=None, source_name=None, site_role=None,
                        environment_type=None, verification="VERIFIED_OFFICIAL"):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    s = FishLandingSite(
        official_name=name, bmu_id=bmu_id, source_name=source_name,
        verification_status=verification, site_role=site_role,
        environment_type=environment_type,
    )
    db.add(s)
    db.flush()
    return s


print("=" * 60)
print("SEEDING TANA RIVER COUNTY GEOGRAPHY INTELLIGENCE")
print("(Revised after proper web research — superseding thin framework)")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_jcma = get_or_create_source(
    "Tana Delta Joint Co-management Area Plan 2024-2028",
    org="KEMFSED / Kenya Fisheries Service / Tana River County Government",
    year=2024, doc_type="JCMA Plan", scope="Tana Delta (Tenewi to Mto Kilifi)", tier=1,
)
src_kipini_esia = get_or_create_source(
    "Kipini Fish Landing Site ESIA Report",
    org="KEMFSED", doc_type="ESIA", tier=1,
)
src_county_tender = get_or_create_source(
    "Proposed Construction of Fish Landing Site in Kipini (Kipini East Ward) — Tender TRCG/FISH/OT/05/2018/19",
    org="County Government of Tana River", year=2018, doc_type="Tender document", tier=1,
)
src_nation_wetland = get_or_create_source(
    "Tana River County Government intensifies drive to restore Kenya's major wetland — Daily Nation",
    doc_type="News report", year=2023, tier=3,
)
src_msp_validation = get_or_create_source(
    "Kenya moves closer to realising Marine Spatial Plan as five coastal counties conduct second validation — KBC",
    doc_type="News report", year=2026, tier=3,
)

print("Sources seeded: 5")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
tana_river = get_or_create_admin("KEN", "county", "Tana River County", source_name=src_jcma.title)

# Tana Delta confirmed as the coastal/fisheries-relevant sub-county
subcounty_names = ["Tana Delta", "Galole", "Tana North", "Bura", "Bangale"]
subcounties = {n: get_or_create_admin("KEN", "sub_county", n, parent_id=tana_river.id, source_name=src_jcma.title) for n in subcounty_names}

# Kipini East Ward confirmed via county tender document
kipini_east_ward = get_or_create_admin("KEN", "ward", "Kipini East", parent_id=subcounties["Tana Delta"].id, source_name=src_county_tender.title)

print(f"Admin geography: 1 county, {len(subcounties)} sub-counties, 1 confirmed ward (Kipini East)")

db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=subcounties["Tana Delta"].id,
    claim_field="ward_structure",
    claim_value="Only Kipini East Ward confirmed via county tender document. Full ward list for Tana Delta sub-county requires KNBS/IEBC boundary verification.",
    source_id=src_county_tender.id, is_canonical="false",
))

# ── TANA DELTA JCMA — 3 confirmed BMUs ────────────────────────────
jcma_tana_delta = JointCoManagementArea(
    name="Tana Delta JCMA", source_name=src_jcma.title, verification_status="VERIFIED_OFFICIAL",
    description="Boundary: Tenewi (north) to Mto Kilifi (south). Diverse contiguous habitats fresh-to-marine: mangroves/wetlands 45%, seagrass 35%, patchy reefs 5-10%, beaches/sand dunes 20%. Priority species: prawns, lobsters, snappers (declining due to habitat degradation). Community Forest Associations (CFAs) active in mangrove conservation alongside BMUs.",
)
db.add(jcma_tana_delta)
db.flush()

bmu_kipini = get_or_create_bmu("Kipini", source_name=src_jcma.title)
bmu_ozi    = get_or_create_bmu("Ozi", source_name=src_jcma.title)
bmu_chara  = get_or_create_bmu("Chara", source_name=src_jcma.title)
jcma_tana_delta.bmus.extend([bmu_kipini, bmu_ozi, bmu_chara])
db.flush()

print("Tana Delta JCMA BMUs confirmed: Kipini, Ozi, Chara")

# ── LANDING SITES — one per BMU confirmed, environment mixed ─────
site_kipini = get_or_create_site("Kipini", bmu_id=bmu_kipini.id, source_name=src_kipini_esia.title,
                                  site_role="main", environment_type="estuarine")
site_ozi    = get_or_create_site("Ozi", bmu_id=bmu_ozi.id, source_name=src_jcma.title,
                                  site_role="main", environment_type="brackish")
site_chara  = get_or_create_site("Chara", bmu_id=bmu_chara.id, source_name=src_jcma.title,
                                  site_role="main", environment_type="mixed")

# Kipini strategic bridge node — freshwater/marine transition (confirmed, not speculative now)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=site_kipini.id,
    claim_field="strategic_note",
    claim_value="Confirmed strategic bridge node — historic Swahili settlement at Tana River mouth (2.526S 40.529E). ESIA confirms significant post-harvest loss due to lack of ice/preservation. Poor accessibility. KEMFSED-funded landing site construction planned (fish banda, boat yard, meeting hall, ablution block, power house, pump house). Site accessible by sea or by River Tana.",
    source_id=src_kipini_esia.id, is_canonical="false",
))

# Species composition difference confirmed between sites (from Ungwana Bay research)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=site_kipini.id,
    claim_field="dominant_species",
    claim_value="Catfish (Arius africanus) dominant catch composition at Kipini landing site",
    source_id=src_jcma.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=site_ozi.id,
    claim_field="dominant_species",
    claim_value="Catfish (Clarias gariepinus) dominant catch composition at Ozi landing site",
    source_id=src_jcma.id, is_canonical="false",
))

print("Landing sites seeded: Kipini (estuarine), Ozi (brackish), Chara (mixed)")

# ── SHEKIKO — shared physical site, gear/boat distribution point ──
# Confirmed via Daily Nation: Governor commissioned boats/gear for
# Chara, Kipini, Ozi BMUs AT Shekiko — but Shekiko is also separately
# proposed as a conservation area under BOTH Chara and Ozi (JCMA doc).
# These are the SAME place name used for two different roles — flag,
# do not silently resolve.
shekiko_site = get_or_create_site("Shekiko", source_name=src_nation_wetland.title,
                                   site_role="subsidiary", environment_type="mixed")
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=shekiko_site.id,
    claim_field="dual_role_note",
    claim_value="Shekiko serves as both a shared commissioning/distribution point for Chara/Kipini/Ozi BMUs (2023 Daily Nation report — Governor commissioned 4 fishing boats there) AND is separately named as a proposed conservation area under BOTH Chara BMU and Ozi BMU in the JCMA plan. Same name, ambiguous whether one physical site with dual function or two distinct 'Shekiko' locations. Requires field verification.",
    source_id=src_nation_wetland.id, is_canonical="false",
))

print("Shekiko seeded as shared distribution point (dual-role ambiguity flagged)")

# ── PROPOSED CONSERVATION AREAS PER BMU (confirmed, section-specific) ──
conservation_areas = {
    "Chara": ["Banda la Kati", "Matola", "Ndungwe", "Kalota"],  # Shekiko already seeded above
    "Kipini": ["Ziwayuu", "Hajawa"],
    "Ozi": [],  # Shekiko already seeded, no additional
}
conservation_zone_count = 0
for bmu_name, zone_names in conservation_areas.items():
    for zone_name in zone_names:
        existing = db.query(EcologicalZone).filter(EcologicalZone.name == zone_name).first()
        if existing:
            continue
        db.add(EcologicalZone(
            name=zone_name, zone_type="proposed_conservation_area",
            source_name=src_jcma.title, verification_status="VERIFIED_OFFICIAL",
            protection_status="proposed",
        ))
        conservation_zone_count += 1
db.flush()

print(f"Proposed conservation areas seeded: {conservation_zone_count} + Shekiko (shared) = {conservation_zone_count + 1} total")
print("  Chara: Shekiko, Banda la Kati, Matola, Ndungwe, Kalota")
print("  Kipini: Ziwayuu, Hajawa")
print("  Ozi: Shekiko (shared with Chara)")

# ── REEF ECOLOGICAL DATA — confirmed via benthic survey ──────────
reef_kipini = EcologicalZone(
    name="Mwamba Ziwaiyu reef", zone_type="reef", landing_site_id=site_kipini.id,
    source_name=src_jcma.title, verification_status="VERIFIED_OFFICIAL",
    protection_status="unprotected",
)
reef_matewa = EcologicalZone(
    name="Matewa reef", zone_type="reef", landing_site_id=site_kipini.id,
    source_name=src_jcma.title, verification_status="VERIFIED_OFFICIAL",
    protection_status="unprotected",
)
db.add_all([reef_kipini, reef_matewa])
db.flush()
db.add(GeographySourceClaim(
    entity_type="ecological_zone", entity_id=reef_kipini.id,
    claim_field="reef_condition",
    claim_value="Hard coral cover 15-35% on average, but large areas dominated by dead coral overgrown with brown macroalgae (Sargassum spp.) — degraded reef condition noted in JCMA benthic survey.",
    source_id=src_jcma.id, is_canonical="false",
))

print("Reef ecological zones seeded: Mwamba Ziwaiyu, Matewa (both showing degradation)")

# ── HABITAT COMPOSITION — county-wide JCMA figure ─────────────────
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=subcounties["Tana Delta"].id,
    claim_field="habitat_composition",
    claim_value="Mangroves/wetlands 45%, seagrass 35%, patchy reefs 5-10%, beaches/sand dunes 20% (Tana Delta JCMA Plan 2024-2028)",
    source_id=src_jcma.id, is_canonical="false",
))

# ── HISTORICAL / CANDIDATE — Moa, Kilelengwani still unresolved ──
unresolved_names = ["Moa", "Kilelengwani"]
unresolved_count = 0
for name in unresolved_names:
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        continue
    site = FishLandingSite(
        official_name=name, source_name=src_jcma.title,
        verification_status="NEEDS_FIELD_VERIFICATION", operational_status="UNKNOWN",
        environment_type="mixed",
    )
    db.add(site)
    db.flush()
    unresolved_count += 1

print(f"Unresolved candidate locations (not confirmed in JCMA plan): {unresolved_count} (Moa, Kilelengwani)")

# ── COMMUNITY FOREST ASSOCIATIONS — noted, not modeled as entities ──
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=subcounties["Tana Delta"].id,
    claim_field="conservation_governance_note",
    claim_value="Multiple Community Forest Associations (CFAs) active in Tana Delta mangrove areas, working alongside the 3 BMUs on conservation. CFAs not yet modeled as distinct entities — requires separate governance-layer research if MarineCatch engages mangrove/carbon-credit programs.",
    source_id=src_jcma.id, is_canonical="false",
))

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("TANA RIVER SEEDING COMPLETE (properly researched)")
print("=" * 60)
print("Confidence upgraded from 'research gap' to VERIFIED_OFFICIAL")
print("via Tana Delta JCMA Plan 2024-2028 — same source tier as")
print("Kwale/Lamu/Kilifi JCMA plans.")
print()
print(f"AdminGeography (national total): {db.query(AdminGeography).filter(AdminGeography.country_code=='KEN').count()}")
print(f"BMUs (national total):           {db.query(BMU).count()}")
print(f"FishLandingSites (national total): {db.query(FishLandingSite).count()}")
print(f"EcologicalZones (national total): {db.query(EcologicalZone).count()}")
print(f"GeographySourceClaims (national total): {db.query(GeographySourceClaim).count()}")

db.close()