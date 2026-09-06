# scripts/seed_kilifi_geography.py
#
# Seeds Kilifi County geography intelligence — Phase 3.
# Preserves TAMKIBO (23 sites/4 BMUs), KAMAMKUKI (34 sites/5 BMUs),
# Malindi-Magarini (5 BMUs, subsidiary sites flagged as research gap
# per package section 9 — NOT invented). Historical major/designated
# sites from 2018 CIDP kept as separate confidence tier from JCMA data.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.geographic_alias import GeographicAlias
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.comanagement import JointCoManagementArea
from app.models.intelligence.county_landing_baseline import CountyLandingBaseline

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


def get_or_create_site(name, bmu_id=None, source_name=None, site_role=None,
                        aggregates_to=None, node_functions=None, verification="RESEARCH_SOURCE"):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    s = FishLandingSite(
        official_name=name, bmu_id=bmu_id, source_name=source_name,
        verification_status=verification, site_role=site_role,
        aggregates_to_site_id=aggregates_to, node_functions=node_functions,
    )
    db.add(s)
    db.flush()
    return s


def add_alias(entity_type, canonical_id, alias_name, confidence="MEDIUM", source_name=None):
    existing = db.query(GeographicAlias).filter(
        GeographicAlias.entity_type == entity_type,
        GeographicAlias.canonical_entity_id == canonical_id,
        GeographicAlias.alias_name == alias_name,
    ).first()
    if existing:
        return existing
    a = GeographicAlias(entity_type=entity_type, canonical_entity_id=canonical_id,
                         alias_name=alias_name, confidence=confidence)
    db.add(a)
    db.flush()
    return a


print("=" * 60)
print("SEEDING KILIFI COUNTY GEOGRAPHY INTELLIGENCE")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_cidp2018 = get_or_create_source(
    "Kilifi County Integrated Development Plan 2018-2022",
    org="County Government of Kilifi", year=2018, doc_type="CIDP", tier=1,
)
src_tamkibo = get_or_create_source(
    "TAMKIBO Joint Co-Management Area Plan 2024-2028",
    org="KEMFSED / Kenya Fisheries Service / Kilifi County Government",
    year=2024, doc_type="JCMA Plan", scope="Kilifi North (Takaungu-Mnarani-Kilifi Central-Bofa)", tier=1,
)
src_kamamkuki = get_or_create_source(
    "KAMAMKUKI JCMA Plan 2024-2028",
    org="KEMFSED / Kenya Fisheries Service", year=2024,
    doc_type="JCMA Plan", scope="Kuruwitu-Kanamai-Kidongo-Marina-Mtwapa", tier=1,
)
src_malindi_magarini = get_or_create_source(
    "Malindi-Magarini JCMA Plan 2024-2028",
    org="KEMFSED / Kenya Fisheries Service / Kilifi County Government",
    year=2024, doc_type="JCMA Plan", scope="Malindi-Magarini", tier=1,
)
src_kilifi_central_assessment = get_or_create_source(
    "Kilifi Central landing-site assessment",
    doc_type="Site assessment", tier=2,
)

print("Sources seeded: 5")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
kilifi = get_or_create_admin("KEN", "county", "Kilifi County", source_name=src_cidp2018.title)

subcounty_names = ["Kilifi North", "Kilifi South", "Ganze", "Malindi", "Magarini", "Kaloleni", "Rabai"]
subcounties = {n: get_or_create_admin("KEN", "sub_county", n, parent_id=kilifi.id, source_name=src_cidp2018.title) for n in subcounty_names}

ward_map = {
    "Kilifi North": ["Tezo", "Sokoni", "Kibarani", "Dabaso", "Matsangoni", "Watamu", "Mnarani"],
    "Kilifi South": ["Shimo la Tewa", "Mtepeni", "Junju", "Chasimba", "Mwarakaya"],
    "Ganze": ["Ganze", "Bamba", "Jaribuni", "Sokoke"],
    "Malindi": ["Malindi Town", "Shella", "Ganda", "Jilore", "Kakuyuni"],
    "Magarini": ["Gongoni", "Magarini", "Adu", "Sabaki", "Garashi", "Marafa"],
    "Kaloleni": ["Kaloleni", "Kayafungo", "Mwanamwinga", "Mariakani"],
    "Rabai": ["Rabai/Kisurutini", "Ruruma", "Kambe/Ribe", "Mwawesa"],
}
wards = {}
for sc_name, ward_list in ward_map.items():
    for w in ward_list:
        wards[w] = get_or_create_admin("KEN", "ward", w, parent_id=subcounties[sc_name].id, source_name=src_cidp2018.title)

print(f"Admin geography: 1 county, {len(subcounties)} sub-counties, {len(wards)} wards")

# ── PRODUCTION FIGURE CONFLICTS (section 18) — NOT merged ────────
prod_conflicts = [
    ("annual_production_tonnes", "2561 MT (2017)", src_cidp2018.id),
    ("annual_production_tonnes", "1611 MT (2021-2022)", src_tamkibo.id),
    ("annual_production_tonnes", "2885 MT annual average (site-development assessment)", src_kilifi_central_assessment.id),
]
for field, value, source_id in prod_conflicts:
    db.add(GeographySourceClaim(
        entity_type="admin_geography", entity_id=kilifi.id,
        claim_field=field, claim_value=value, source_id=source_id, is_canonical="false",
    ))
db.flush()
print(f"Production figure conflicts preserved: {len(prod_conflicts)}")

# ── TAMKIBO JCMA — 4 BMUs, 23 landing sites ──────────────────────
tamkibo_bmu_names = ["Takaungu", "Mnarani", "Kilifi Central", "Bofa"]
tamkibo_bmus = {n: get_or_create_bmu(n, source_name=src_tamkibo.title, active_status="ACTIVE") for n in tamkibo_bmu_names}

jcma_tamkibo = JointCoManagementArea(
    name="TAMKIBO JCMA", source_name=src_tamkibo.title, verification_status="VERIFIED_OFFICIAL",
    description="1324 registered members: 791 fishers, 157 boat owners, 256 traders, 276 fish mongers, 1 loader. 84 shared fishing grounds.",
)
db.add(jcma_tamkibo)
db.flush()
jcma_tamkibo.bmus.extend(tamkibo_bmus.values())

tamkibo_sites_map = {
    "Takaungu": ["Vuma", "Vitanga Viwili", "Kitangani", "Customs / Madauni", "Chaurembo", "Mlangoni", "Ngazini"],
    "Mnarani": ["Mnarani", "Kidundu", "Mtongani", "Red House"],
    "Kilifi Central": ["Old Ferry", "Maringoni", "Kibokoni", "Kuchi / Laini", "Maya"],
    "Bofa": ["Veterinary", "Baobab", "Vidazini", "Kilifi Bay", "Bofa Main", "Kwa Ngala", "Kipangani"],
}
tamkibo_site_count = 0
kilifi_central_site = None
for bmu_name, sites in tamkibo_sites_map.items():
    bmu_obj = tamkibo_bmus[bmu_name]
    for site_name in sites:
        role = "main" if site_name in ("Old Ferry", "Mnarani", "Bofa Main", "Vuma") else "subsidiary"
        node_fn = None
        if site_name == "Old Ferry":
            # Kilifi Central / Old Ferry — regional aggregation hub, section 15
            node_fn = "LANDING,AGGREGATION"
        s = get_or_create_site(site_name, bmu_id=bmu_obj.id, source_name=src_tamkibo.title,
                                site_role=role, node_functions=node_fn)
        if site_name == "Old Ferry":
            kilifi_central_site = s
        tamkibo_site_count += 1

add_alias("fish_landing_site", kilifi_central_site.id, "Kilifi Central", confidence="HIGH", source_name=src_kilifi_central_assessment.title)
add_alias("fish_landing_site", kilifi_central_site.id, "Old Ferry-Kilifi", confidence="MEDIUM")

# Kilifi Central as aggregation hub for adjacent sites (section 15: ~70% of catch)
adjacent_to_central = ["Bofa Main", "Mnarani", "Kuchi / Laini", "Kibokoni", "Maya", "Maringoni", "Kitangani"]
for name in adjacent_to_central:
    site = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if site:
        site.aggregates_to_site_id = kilifi_central_site.id
db.flush()

db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=kilifi_central_site.id,
    claim_field="aggregation_share",
    claim_value="~542 MT reported July 2021-June 2022 across Kilifi Central + adjacent sites; Kilifi Central ~70% of that catch",
    source_id=src_kilifi_central_assessment.id, is_canonical="false",
))

print(f"TAMKIBO landing sites: {tamkibo_site_count}, Kilifi Central marked as aggregation hub for {len(adjacent_to_central)} adjacent sites")

# ── KAMAMKUKI JCMA — 5 BMUs, 34 landing sites ────────────────────
kamamkuki_bmu_names = ["Kuruwitu", "Kanamai", "Kidongo", "Marina", "Mtwapa"]
kamamkuki_bmus = {n: get_or_create_bmu(n, source_name=src_kamamkuki.title, active_status="ACTIVE") for n in kamamkuki_bmu_names}

jcma_kamamkuki = JointCoManagementArea(
    name="KAMAMKUKI JCMA", source_name=src_kamamkuki.title, verification_status="VERIFIED_OFFICIAL",
    description="694 registered members: 476 fishers, 93 boat owners, 130 fish traders, 85 fish mongers, 2 loaders, 1 food vendor. 47 key fishing grounds.",
)
db.add(jcma_kamamkuki)
db.flush()
jcma_kamamkuki.bmus.extend(kamamkuki_bmus.values())

kamamkuki_sites_map = {
    "Kuruwitu": ["Mwanamia", "Kijangwani", "Kuruwitu", "Kinuni", "Vipingo", "Bureni"],
    "Kanamai": ["Jumba Ruins", "Ndodo", "Mwendo wa Panya", "Kanamai", "Whispering", "Sun and Sand", "Karkland", "Ngoloko", "Kazungu wa Shungu", "Msumarini"],
    "Kidongo": ["Old Ferry (Mtwapa)", "Bemnyazi", "Mwakusea", "Kwa Kilo", "Mibuyuni", "Chigozani", "Kidongo"],
    "Marina": ["Shanzu", "Navy Barracks", "Mtwapa Bridge"],
    "Mtwapa": ["Moorings", "Babylon", "Kwa Chief", "Customs", "Kichangani", "Vingazini", "Mkomani", "Jumba Ruins"],
}
kamamkuki_site_count = 0
for bmu_name, sites in kamamkuki_sites_map.items():
    bmu_obj = kamamkuki_bmus[bmu_name]
    for site_name in sites:
        existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == site_name).first()
        if existing:
            kamamkuki_site_count += 1
            continue  # "Jumba Ruins" appears twice in source (Kanamai + Mtwapa) — kept as one record
        get_or_create_site(site_name, bmu_id=bmu_obj.id, source_name=src_kamamkuki.title, site_role="subsidiary")
        kamamkuki_site_count += 1

add_alias("fish_landing_site",
          db.query(FishLandingSite).filter(FishLandingSite.official_name == "Old Ferry (Mtwapa)").first().id,
          "Mtwapa Old Ferry", confidence="MEDIUM")

print(f"KAMAMKUKI landing sites processed: {kamamkuki_site_count} (Jumba Ruins deduplicated per source note)")

# ── MALINDI-MAGARINI JCMA — 5 BMUs, subsidiary sites = RESEARCH GAP ──
mm_bmu_names = ["Marereni", "Gongoni", "Ngomeni", "Kichwa cha Kati", "Shella"]
mm_bmus = {n: get_or_create_bmu(n, source_name=src_malindi_magarini.title, active_status="ACTIVE") for n in mm_bmu_names}

jcma_mm = JointCoManagementArea(
    name="Malindi-Magarini JCMA", source_name=src_malindi_magarini.title, verification_status="VERIFIED_OFFICIAL",
    description="1338.19 km2, ~46km coastline, Mto-Kilifi to Kivulini. 5 priority fisheries: shallow-water prawn (11%), small-scale tuna (47%), octopus (3%), reef demersal (27%), snapper gillnet (12%).",
)
db.add(jcma_mm)
db.flush()
jcma_mm.bmus.extend(mm_bmus.values())

# Section 9 explicit instruction: do NOT invent subsidiary landing sites.
# Seed each BMU's PRIMARY site only (from CIDP 2018), flag subsidiary
# network as a research gap claim.
mm_primary_sites = {
    "Marereni": "Marereni",
    "Gongoni": "Gongoni",
    "Ngomeni": "Ngomeni",
    "Shella": "Shella",
}
for bmu_name, site_name in mm_primary_sites.items():
    get_or_create_site(site_name, bmu_id=mm_bmus[bmu_name].id, source_name=src_cidp2018.title,
                        site_role="main")

# Kichwa cha Kati has no CIDP 2018 entry but is confirmed infrastructure-priority (section 14)
kck_site = get_or_create_site("Kichwa cha Kati", bmu_id=mm_bmus["Kichwa cha Kati"].id,
                                source_name=src_malindi_magarini.title, site_role="main")

for bmu_name, bmu_obj in mm_bmus.items():
    db.add(GeographySourceClaim(
        entity_type="bmu", entity_id=bmu_obj.id,
        claim_field="subsidiary_landing_sites",
        claim_value="RESEARCH GAP — Malindi-Magarini JCMA plan does not publish a clean BMU-to-subsidiary-site table like TAMKIBO/KAMAMKUKI. Requires KeFS/County Fisheries Directorate/BMU register verification before subsidiary sites can be seeded.",
        source_id=src_malindi_magarini.id, is_canonical="false",
    ))
db.flush()

print(f"Malindi-Magarini BMUs: {len(mm_bmus)}, primary sites seeded: {len(mm_primary_sites) + 1}")
print("  Subsidiary landing sites flagged as RESEARCH GAP (section 9) — not invented")

# ── HISTORICAL 2018 CIDP MAJOR/DESIGNATED SITES (section 3) ──────
# Fundissa listed separately under Marereni BMU per source
fundissa = get_or_create_site("Fundissa", bmu_id=mm_bmus["Marereni"].id, source_name=src_cidp2018.title, site_role="subsidiary")

# Watamu and Mayungu BMUs referenced in 2018 CIDP but not in current JCMA plans reviewed
bmu_watamu = get_or_create_bmu("Watamu", source_name=src_cidp2018.title, active_status="UNKNOWN")
bmu_mayungu = get_or_create_bmu("Mayungu", source_name=src_cidp2018.title, active_status="UNKNOWN")
site_watamu = get_or_create_site("Watamu", bmu_id=bmu_watamu.id, source_name=src_cidp2018.title,
                                  site_role="main", node_functions="LANDING,INSTITUTIONAL")
# Billfish tourism/high-value tag (section 16)
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=site_watamu.id,
    claim_field="fishery_classification",
    claim_value="HIGH_VALUE_FISHERY: billfish/sportfishing hub per recent billfish research",
    source_id=src_cidp2018.id, is_canonical="false",
))
site_mayungu = get_or_create_site("Mayungu", bmu_id=bmu_mayungu.id, source_name=src_cidp2018.title, site_role="main")

print("2018 CIDP historical additions: Fundissa, Watamu BMU/site, Mayungu BMU/site")

# ── 2024 COUNTY LANDING BASELINE (partial — Kilifi total not given, ─
# only sub-figures in package; skip county-level baseline row since
# package explicitly separates 2017/2021-22/site-assessment figures
# as conflicting claims rather than one clean total — already captured above)

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("KILIFI SEEDING COMPLETE")
print("=" * 60)
print(f"AdminGeography (national total): {db.query(AdminGeography).filter(AdminGeography.country_code=='KEN').count()}")
print(f"BMUs (national total):           {db.query(BMU).count()}")
print(f"FishLandingSites (national total): {db.query(FishLandingSite).count()}")
print(f"JointCoManagementAreas (national total): {db.query(JointCoManagementArea).count()}")
print(f"GeographySourceClaims (national total): {db.query(GeographySourceClaim).count()}")

db.close()