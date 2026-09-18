# scripts/seed_zanzibar_unguja_phase1.py
#
# Zanzibar / Unguja Phase 1 seed — Tiers A/B/C only, per the
# confidence-tiered handoff. Does NOT seed the full 235-site
# universe, the unverified SFC count (~91), or unconfirmed CMG
# membership. Tier D items are recorded as GeographySourceClaim
# gap markers, not invented rows.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.comanagement import MarineManagementArea

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, doc_type=None, tier=2):
    existing = db.query(GeographySource).filter(GeographySource.title == title).first()
    if existing:
        return existing
    s = GeographySource(title=title, issuing_organization=org, publication_year=year,
                         document_type=doc_type, reliability_tier=tier)
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


def get_or_create_site(name, village=None, district=None, source_name=None,
                        vessel_count=None, data_stage="survey_identified",
                        classification=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    s = FishLandingSite(
        official_name=name, local_name=village, source_name=source_name,
        verification_status="RESEARCH_SOURCE", data_verification_stage=data_stage,
        estimated_boat_count=vessel_count, site_classification=classification,
        production_system="wild_capture",
    )
    db.add(s)
    db.flush()
    return s


print("=" * 60)
print("SEEDING ZANZIBAR / UNGUJA — PHASE 1")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_jica2024 = get_or_create_source(
    "JICA Fisheries Sector Survey (reporting 2020 Zanzibar Frame Survey)",
    org="JICA", year=2024, doc_type="Frame survey / sector report", tier=1,
)
src_khatib_jiddawi = get_or_create_source(
    "2020 review of Zanzibar fisheries (Khatib & Jiddawi dataset)",
    year=2020, doc_type="Secondary review", tier=2,
)
src_fao1985 = get_or_create_source(
    "FAO-hosted Zanzibar fisheries survey (historical sampling frame)",
    org="FAO", year=1985, doc_type="Historical survey", tier=2,
)
src_mca_recent = get_or_create_source(
    "Recent gazetted MCA/MPA list for Zanzibar",
    doc_type="Governance record", tier=1,
)

print("Sources seeded: 4")

# ── ADMIN GEOGRAPHY — Zanzibar > Unguja > Region > District > Shehia ──
zanzibar = get_or_create_admin("TZA", "semi_autonomous_region", "Zanzibar", source_name=src_jica2024.title)
unguja   = get_or_create_admin("TZA", "island", "Unguja", parent_id=zanzibar.id, source_name=src_jica2024.title)

unguja_regions = {
    "Kaskazini Unguja": get_or_create_admin("TZA", "region", "Kaskazini Unguja", parent_id=unguja.id),
    "Kusini Unguja":     get_or_create_admin("TZA", "region", "Kusini Unguja", parent_id=unguja.id),
    "Mjini Magharibi":    get_or_create_admin("TZA", "region", "Mjini Magharibi", parent_id=unguja.id),
}

unguja_district_map = {
    "Kaskazini Unguja": ["North A", "North B"],
    "Kusini Unguja":     ["Central", "South"],
    "Mjini Magharibi":    ["West A", "West B", "Urban"],
}
unguja_districts = {}
for region_name, district_list in unguja_district_map.items():
    for d in district_list:
        unguja_districts[d] = get_or_create_admin("TZA", "district", d, parent_id=unguja_regions[region_name].id)

print(f"Admin geography: Zanzibar > Unguja > {len(unguja_regions)} regions > {len(unguja_districts)} districts")

db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=unguja.id,
    claim_field="shehia_count",
    claim_value="Shehia is a real administrative/community layer below district (e.g. Wete District mainland-side lists 36 Shehias) — full Unguja Shehia registry not yet extracted",
    source_id=src_jica2024.id, is_canonical="false",
))

# ── LANDING SITE COUNT CONFLICTS — 4 sources, none reconciled ──────
count_conflicts = [
    ("landing_site_count", "26+ documented sampling sites (1985 FAO-hosted survey, historical frame — never mix with modern counts)", src_fao1985.id),
    ("landing_site_count", "224 landing sites (2020 review, Khatib & Jiddawi-derived estimate)", src_khatib_jiddawi.id),
    ("landing_site_count", "109 Unguja landing sites of 235 total (2020 Zanzibar Frame Survey)", src_jica2024.id),
    ("landing_site_count", "21 Unguja sites field-confirmed during JICA field verification (of 235 identified)", src_jica2024.id),
]
for field, value, source_id in count_conflicts:
    db.add(GeographySourceClaim(
        entity_type="admin_geography", entity_id=unguja.id,
        claim_field=field, claim_value=value, source_id=source_id, is_canonical="false",
    ))
db.flush()
print(f"Landing-site count conflicts preserved: {len(count_conflicts)}")

# ── TIER A — 13 high-vessel Unguja landing sites ──────────────────
unguja_high_vessel = [
    ("Kizimkazi",  "Mkunguni",          "South",     211),
    ("Kigomani",   "Tundangaa",         "North A",   182),
    ("Nungwi",     "Cha Nungwi",        "North A",   156),
    ("Funguni",    "Mwanbele",          "North A",   153),
    ("Mazizini",   "Kiembe Samaki",     "West B",    146),
    ("Mangapwani", "Mchangani Mangapwani","North B", 139),
    ("Dikokuu",    "Chwaka",            "Central",   126),
    ("Bambuu",     "Chem-Chem",         "West A",    126),
    ("Fumba Ziwani","Fumba",            "West B",    123),
    ("Sharifumsa", "Sharifumsa",        "West A",    122),
    ("Buyu",       "Chukwani",          "West B",    115),
    ("Muwange",    "Pita Na Zako",      "North A",   114),
    ("Kgomeni",    "Mtoni",             "West A",    None),  # vessel count unverified — flagged, not guessed
]
site_count = 0
for name, village, district, vessels in unguja_high_vessel:
    s = get_or_create_site(name, village=village, source_name=src_jica2024.title,
                            vessel_count=vessels, data_stage="confirmed",
                            classification="HIGH_VESSEL_SITE")
    if vessels is None:
        db.add(GeographySourceClaim(
            entity_type="fish_landing_site", entity_id=s.id,
            claim_field="vessel_count",
            claim_value="Source PDF extraction malformed at this value — do not seed a guessed number",
            source_id=src_jica2024.id, is_canonical="false",
        ))
    site_count += 1
print(f"Tier A — high-vessel Unguja sites seeded: {site_count} (Kgomeni vessel count flagged, not guessed)")

# ── TIER A — 4 JICA priority sites (Unguja) with rich notes ────────
priority_sites_unguja = {
    "Nungwi": {
        "notes": "~200 fishing vessels observed/estimated; ~1,300 beneficiary fishers (JICA assessment); tourist economy surrounding site; auction and retail facilities; fishing-committee management; electricity/water access; significant commercial activity.",
    },
    "Fungu Refu": {
        "notes": "~200 large small-pelagic vessels; ~50 FRP vessels targeting large pelagics; ~1,000 fishers involved; important processing/aggregation potential; ZAFICO investment plans.",
    },
    "Kama": {
        "notes": "~50 vessels; dominated by small-pelagic fishing; anchovy processing infrastructure; women involved in processing; ZAFICO processing investment.",
    },
    "Kizimkazi": {
        "notes": "~130 registered vessels (JICA description); ~230 fishers; seasonal migration from Nungwi and Pemba; hotel/tourism buyers; local and urban middlemen.",
    },
}
for name, data in priority_sites_unguja.items():
    s = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if not s:
        s = get_or_create_site(name, source_name=src_jica2024.title, data_stage="confirmed")
    s.site_classification = (s.site_classification or "") + ",JICA_PRIORITY_SITE,DETAILED_ASSESSMENT"
    db.add(GeographySourceClaim(
        entity_type="fish_landing_site", entity_id=s.id,
        claim_field="operational_detail", claim_value=data["notes"],
        source_id=src_jica2024.id, is_canonical="false",
    ))
db.flush()
print(f"Tier A — JICA priority sites enriched with operational notes: {len(priority_sites_unguja)}")

# ── TIER A — 6 gazetted MCAs (seeded once here, referenced by both scripts) ──
mca_list = [
    ("Menai Bay Conservation Area", "MBCA"),
    ("Mnemba Island–Chwaka Bay Marine Conservation Area", "MIMCA"),
    ("Pemba Channel Conservation Area", "PECCA"),
    ("Chumbe Island Coral Park", "CHICOP"),
    ("Tumbatu Marine Conservation Area", "TUMCA"),
    ("Changuu–Bawe Marine Conservation Area", "CHABAMCA"),
]
mca_count = 0
for full_name, abbrev in mca_list:
    existing = db.query(MarineManagementArea).filter(MarineManagementArea.designation == full_name).first()
    if not existing:
        db.add(MarineManagementArea(
            designation=full_name, source_name=src_mca_recent.title,
            verification_status="VERIFIED_OFFICIAL", notes=f"Abbreviation: {abbrev}" if hasattr(MarineManagementArea, 'notes') else None,
        ))
        mca_count += 1
db.flush()
print(f"6 gazetted MCAs seeded: {mca_count} new (some may already exist from prior runs)")

# ── TIER D — explicit gap markers, nothing invented ─────────────────
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=unguja.id,
    claim_field="research_gap",
    claim_value="Complete 235-site name registry NOT recovered. Only 13 high-vessel + 4 JICA priority Unguja sites (17 total, overlapping) seeded this phase. Remaining ~92 Unguja sites (109 total minus 17 seeded) require dedicated extraction/field-validation pass.",
    source_id=src_jica2024.id, is_canonical="false",
))

db.commit()

print()
print("=" * 60)
print("ZANZIBAR / UNGUJA PHASE 1 COMPLETE")
print("=" * 60)
print(f"FishLandingSites (Unguja, this script): {site_count} + priority-site enrichment on 4")
print(f"MarineManagementAreas (Zanzibar-wide, seeded here): {mca_count}")
print("Tier D gap explicitly recorded — no invented sites")

db.close()