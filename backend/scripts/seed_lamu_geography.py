# scripts/seed_lamu_geography.py
#
# Seeds Lamu County geography intelligence — Phase 2 of Kenya coastal
# counties. Preserves all conflicts (27 vs 37 BMUs, 35 vs 40+ landing
# sites), all strategic node classifications, tenure risk flags, and
# the KICOWA/Lamu Bay JCMA structures exactly as researched. No
# invented coordinates or counts.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.geographic_alias import GeographicAlias
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.comanagement import JointCoManagementArea
from app.models.intelligence.fishing_gear import FishingGear

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


def get_or_create_bmu(name, source_name=None, active_status="UNKNOWN"):
    existing = db.query(BMU).filter(BMU.official_name == name).first()
    if existing:
        return existing
    b = BMU(official_name=name, source_name=source_name,
            active_status=active_status, verification_status="RESEARCH_SOURCE")
    db.add(b)
    db.flush()
    return b


def get_or_create_site(name, bmu_id=None, source_name=None, classification=None,
                        is_island=None, tenure=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    s = FishLandingSite(
        official_name=name, bmu_id=bmu_id, source_name=source_name,
        verification_status="RESEARCH_SOURCE",
        site_classification=classification, is_island=is_island,
        land_tenure_status=tenure,
    )
    db.add(s)
    db.flush()
    return s


print("=" * 60)
print("SEEDING LAMU COUNTY GEOGRAPHY INTELLIGENCE")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_kemfsed = get_or_create_source(
    "KEMFSED Lamu BMU/co-management documentation",
    org="KEMFSED", doc_type="Co-management documentation", tier=2,
)
src_lamu_bay_jcma = get_or_create_source(
    "Lamu Bay Joint Co-management Area Plan 2024-2028",
    org="County Government of Lamu / KEMFSED", year=2024,
    doc_type="JCMA Plan", scope="Lamu Bay", tier=1,
)
src_historical = get_or_create_source(
    "Historical Lamu fisheries sampling datasets",
    doc_type="Historical dataset", tier=4,
)
src_county_lamu = get_or_create_source(
    "County Government of Lamu administrative records",
    org="County Government of Lamu", doc_type="County records", tier=1,
)

print("Sources seeded: 4")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
lamu = get_or_create_admin("KEN", "county", "Lamu County", source_name=src_county_lamu.title)

subcounties = {
    "Lamu East": get_or_create_admin("KEN", "sub_county", "Lamu East", parent_id=lamu.id, source_name=src_county_lamu.title),
    "Lamu West": get_or_create_admin("KEN", "sub_county", "Lamu West", parent_id=lamu.id, source_name=src_county_lamu.title),
}

ward_map = {
    "Lamu East": ["Faza", "Kiunga", "Basuba"],
    "Lamu West": ["Shella", "Mkomani", "Hindi", "Mkunumbi", "Hongwe", "Bahari", "Witu"],
}
wards = {}
for sc_name, ward_list in ward_map.items():
    for w in ward_list:
        wards[w] = get_or_create_admin("KEN", "ward", w, parent_id=subcounties[sc_name].id, source_name=src_county_lamu.title)

print(f"Admin geography: 1 county, {len(subcounties)} sub-counties, {len(wards)} wards")

# ── SOURCE CLAIM CONFLICTS (section 12) ──────────────────────────
conflicts = [
    ("bmu_count", "27 BMUs (current KEMFSED structure)", src_kemfsed.id),
    ("bmu_count", "37 BMUs (older sources, ~4500-4734 members/fishers)", src_historical.id),
    ("landing_site_count", "28 fish landing sites (2014 report)", src_historical.id),
    ("landing_site_count", "35 landing sites (Lamu Bay JCMA 2024-2028, verified)", src_lamu_bay_jcma.id),
    ("landing_site_count", "40+ landing sites (recent reporting)", src_kemfsed.id),
]
for field, value, source_id in conflicts:
    db.add(GeographySourceClaim(
        entity_type="admin_geography", entity_id=lamu.id,
        claim_field=field, claim_value=value, source_id=source_id, is_canonical="false",
    ))
db.flush()
print(f"Source conflicts preserved: {len(conflicts)}")

# ── LAMU BAY JCMA — 10 BMUs, 35 verified landing sites ───────────
jcma_lamu_bay = JointCoManagementArea(
    name="Lamu Bay JCMA", source_name=src_lamu_bay_jcma.title,
    verification_status="VERIFIED_OFFICIAL",
    description="1552 registered members, 1177 fishers, 345 boat owners, 145 fish traders, 168 fish mongers, 62 loaders, 270 net repairers, 67 boat repairers",
)
db.add(jcma_lamu_bay)
db.flush()

lamu_bay_bmus = {}
for name in ["Amu", "Shella Manda", "Matondoni", "Mashundwani", "Bandari Salama",
             "Ndambwe", "Mkunumbi", "Kipungani", "Kiongwe Mjini", "Mea"]:
    b = get_or_create_bmu(name, source_name=src_lamu_bay_jcma.title, active_status="ACTIVE")
    lamu_bay_bmus[name] = b
jcma_lamu_bay.bmus.extend(lamu_bay_bmus.values())

print(f"Lamu Bay JCMA BMUs: {len(lamu_bay_bmus)}")

lamu_bay_sites_map = {
    "Amu": ["Langoni", "Palace", "Mkomani", "Wiyoni"],
    "Shella Manda": ["Fisheries", "Manda", "Ras Kitau", "Stop Over", "Peponi", "Jua Kali"],
    "Matondoni": ["Matondoni"],
    "Mashundwani": ["Mashundwani"],
    "Bandari Salama": ["Kitangani", "Mokowe Jetty", "Mokowe Old Jetty", "Mokowe Creek", "Bandari Salama"],
    "Ndambwe": ["Ndambwe", "Kizuke", "Funga Mbuzi", "Kitwa cha Nyoka"],
    "Mkunumbi": ["Magandani", "Bandarini"],
    "Kipungani": ["Kipungani", "Kisisi", "Kizingo", "Mwera", "Mtuni", "Kizingoni"],
    "Kiongwe Mjini": ["Mawambwe", "Ngoi", "Zijituni", "Tenewi"],
    "Mea": ["Mea", "Ngorotano"],
}

lamu_bay_site_count = 0
for bmu_name, site_names in lamu_bay_sites_map.items():
    bmu_obj = lamu_bay_bmus[bmu_name]
    for site_name in site_names:
        classification = None
        tenure = None
        is_island = True  # Lamu Bay sites are archipelago/island geography
        if site_name in ("Mokowe Jetty", "Mokowe Old Jetty", "Mokowe Creek", "Bandari Salama"):
            classification = "STRATEGIC_AGGREGATION_NODE"
            tenure = "public_unsecured"  # Mokowe flagged for tenure risk, section 14
        if site_name == "Ras Kitau":
            tenure = "disputed"  # explicitly flagged in section 14
        get_or_create_site(site_name, bmu_id=bmu_obj.id, source_name=src_lamu_bay_jcma.title,
                            classification=classification, is_island=is_island, tenure=tenure)
        lamu_bay_site_count += 1

print(f"Lamu Bay verified landing sites: {lamu_bay_site_count}")

# ── KICOWA NETWORK — 8 BMUs, northern/border corridor ────────────
kicowa_names = ["Kiwayu", "Mkokoni", "Kiunga", "Mwambore", "Mvindeni", "Rubu", "Chandani", "Ishakani"]
kicowa_bmus = {}
for name in kicowa_names:
    b = get_or_create_bmu(name, source_name=src_kemfsed.title, active_status="ACTIVE")
    kicowa_bmus[name] = b
    # Each BMU name also seeded as its own landing site where the BMU name
    # itself denotes the primary landing location (per package section 6)
    classification = "NORTHERN_HUB,CONSERVATION_SENSITIVE,ISLAND_LOGISTICS"
    if name == "Kiunga":
        classification = "NORTHERN_HUB,CONSERVATION_SENSITIVE,ISLAND_LOGISTICS,border_corridor,kiunga_marine_reserve,security_sensitive,remote_logistics"
    get_or_create_site(name, bmu_id=b.id, source_name=src_kemfsed.title,
                        classification=classification, is_island=True)

print(f"KICOWA network BMUs (northern/border corridor): {len(kicowa_bmus)}")

# ── OTHER CURRENT KEMFSED BMUs (27-BMU structure, section 5+12) ──
other_bmu_names = ["Kizingitini", "Ndau", "Faza", "Siu", "Mbwajumwali",
                    "Mtangawanda", "Tchundwa", "Pate", "Shanga"]
other_bmus = {}
for name in other_bmu_names:
    b = get_or_create_bmu(name, source_name=src_kemfsed.title, active_status="ACTIVE")
    other_bmus[name] = b

# Strategic classifications per section 10
strategic_sites = {
    "Kizingitini": "MAJOR_LANDING_HUB,COLD_CHAIN_PRIORITY,EXPORT_POTENTIAL,NORTHERN_CORRIDOR",
    "Faza":        "MAJOR_LANDING_HUB,COLD_CHAIN_NODE,ISLAND_LOGISTICS",
    "Mtangawanda": "LANDING_HUB,INFRASTRUCTURE_PRIORITY",
}
for name, bmu_obj in other_bmus.items():
    classification = strategic_sites.get(name)
    get_or_create_site(name, bmu_id=bmu_obj.id, source_name=src_kemfsed.title,
                        classification=classification, is_island=True)

print(f"Other current KEMFSED BMUs seeded: {len(other_bmus)}")
print("  NOTE: Shanga kept as single record (Ishakani/Rubu variant NOT")
print("  auto-split per section 5 instruction — flagged for field verification)")

db.add(GeographySourceClaim(
    entity_type="bmu", entity_id=other_bmus["Shanga"].id,
    claim_field="possible_subdivision",
    claim_value="Some sources distinguish Shanga Ishakani vs Shanga Rubu — not split without verification",
    source_id=src_kemfsed.id, is_canonical="false",
))

# ── FAZA-SIU-MBWAJUMWALI JCMA + PATE-SHANGA JCMA ─────────────────
jcma_faza = JointCoManagementArea(name="Faza-Siu-Mbwajumwali JCMA", source_name=src_kemfsed.title, verification_status="RESEARCH_SOURCE")
db.add(jcma_faza)
db.flush()
jcma_faza.bmus.extend([other_bmus["Faza"], other_bmus["Siu"], other_bmus["Mbwajumwali"]])

jcma_pate_shanga = JointCoManagementArea(name="Pate-Shanga JCMA", source_name=src_kemfsed.title, verification_status="RESEARCH_SOURCE")
db.add(jcma_pate_shanga)
db.flush()
jcma_pate_shanga.bmus.extend([other_bmus["Pate"], other_bmus["Shanga"]])

print("JCMAs seeded: Faza-Siu-Mbwajumwali, Pate-Shanga (plus Lamu Bay JCMA above)")

# ── HISTORICAL / CANDIDATE LANDING SITES (section 11) ────────────
historical_names = [
    "Fambuzi", "Rasini", "Dodori", "Wange", "Lamu", "Magogoni",
    "Ndununi", "Kipini", "Shekiko",
]
hist_count = 0
for name in historical_names:
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if not existing:
        db.add(FishLandingSite(
            official_name=name, source_name=src_historical.title,
            verification_status="NEEDS_FIELD_VERIFICATION",
            operational_status="UNKNOWN",
        ))
        hist_count += 1
db.flush()

print(f"Historical/candidate landing sites (unverified, flagged): {hist_count}")

# ── FISHING GEAR (section 17) ─────────────────────────────────────
gear_names = ["Handline", "Monofilament nets", "Rods and line", "Prawn seines",
              "Longlines", "Drift nets", "Gillnets", "Scoop nets",
              "Basket traps", "Seine nets", "Spears"]
gear_count = 0
for name in gear_names:
    existing = db.query(FishingGear).filter(FishingGear.name == name).first()
    if not existing:
        db.add(FishingGear(name=name, source_name=src_kemfsed.title, verification_status="RESEARCH_SOURCE"))
        gear_count += 1
db.flush()

print(f"Fishing gears seeded: {gear_count}")

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("LAMU SEEDING COMPLETE")
print("=" * 60)
print(f"AdminGeography records:  {db.query(AdminGeography).filter(AdminGeography.country_code=='KEN').count()} (national total)")
print(f"BMUs (national total):   {db.query(BMU).count()}")
print(f"FishLandingSites (national total): {db.query(FishLandingSite).count()}")
print(f"JointCoManagementAreas (national total): {db.query(JointCoManagementArea).count()}")
print(f"FishingGears:            {db.query(FishingGear).count()}")
print(f"GeographySourceClaims (national total): {db.query(GeographySourceClaim).count()}")

db.close()