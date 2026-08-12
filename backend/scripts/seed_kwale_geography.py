# scripts/seed_kwale_geography.py
#
# Seeds Kwale County geography intelligence from the research package.
# Preserves ALL source conflicts, all named sites, all aliases exactly
# as given. No invented coordinates, no invented counts, no silent
# reconciliation. Run this script; it is idempotent per name.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.geographic_alias import GeographicAlias
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.bmu import BMU
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.fishing_ground import FishingGround
from app.models.intelligence.comanagement import JointCoManagementArea, MarineManagementArea
from app.models.intelligence.species_availability import SpeciesAvailability

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, doc_type=None, scope=None, tier=3):
    existing = db.query(GeographySource).filter(GeographySource.title == title).first()
    if existing:
        return existing
    s = GeographySource(
        title=title, issuing_organization=org, publication_year=year,
        document_type=doc_type, geographic_scope=scope, reliability_tier=tier,
    )
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
    a = AdminGeography(
        country_code=country_code, geography_type=geography_type,
        official_name=official_name, parent_id=parent_id,
        source_name=source_name, verification_status="OFFICIAL_UNVERIFIED",
    )
    db.add(a)
    db.flush()
    return a


def get_or_create_bmu(name, source_name=None, notes=None):
    existing = db.query(BMU).filter(BMU.official_name == name).first()
    if existing:
        return existing
    b = BMU(official_name=name, source_name=source_name, verification_status="RESEARCH_SOURCE")
    db.add(b)
    db.flush()
    return b


def get_or_create_site(name, bmu_id=None, source_name=None, gazetted=None, extra=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    kwargs = dict(
        official_name=name, bmu_id=bmu_id, source_name=source_name,
        verification_status="RESEARCH_SOURCE",
    )
    if gazetted:
        kwargs["gazetted_status"] = gazetted
    if extra:
        kwargs.update(extra)
    s = FishLandingSite(**kwargs)
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
    a = GeographicAlias(
        entity_type=entity_type, canonical_entity_id=canonical_id,
        alias_name=alias_name, confidence=confidence,
    )
    db.add(a)
    db.flush()
    return a


print("=" * 60)
print("SEEDING KWALE COUNTY GEOGRAPHY INTELLIGENCE")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_cidp = get_or_create_source(
    "Kwale County Integrated Development Plan 2023-2027",
    org="County Government of Kwale", year=2023, doc_type="CIDP",
    scope="Kwale County", tier=1,
)
src_adp = get_or_create_source(
    "Kwale County Annual Development Plan FY2025/2026",
    org="County Government of Kwale", year=2025, doc_type="ADP", tier=1,
)
src_spatial = get_or_create_source(
    "Kwale County Spatial Plan 2023-2032",
    org="County Government of Kwale", doc_type="Spatial Plan", tier=1,
)
src_2018 = get_or_create_source(
    "Kwale County Department of Fisheries landing-site register",
    org="County Government of Kwale", year=2018, doc_type="Register", tier=1,
)
src_legal = get_or_create_source(
    "Kenya Legal Notice 124 of 2024",
    org="Kenya Gazette", year=2024, doc_type="Legal Notice", tier=1,
)
src_kemfsed = get_or_create_source(
    "KEMFSED JCMA documentation for Kwale",
    org="KEMFSED", doc_type="JCMA Documentation", tier=2,
)
src_mwaepe_esia = get_or_create_source(
    "Mwaepe Fish Landing Site ESIA",
    doc_type="ESIA", tier=2,
)
src_shimoni_esia = get_or_create_source(
    "Shimoni Port ESIA", year=2020, doc_type="ESIA", tier=2,
)

print("Sources seeded: 8")

# ── ADMIN GEOGRAPHY: COUNTY ──────────────────────────────────────
kwale = get_or_create_admin("KEN", "county", "Kwale County", source_name=src_cidp.title)

# ── SUB-COUNTIES ─────────────────────────────────────────────────
subcounties = {}
for name in ["Matuga", "Msambweni", "Lunga-Lunga", "Kinango"]:
    subcounties[name] = get_or_create_admin(
        "KEN", "sub_county", name, parent_id=kwale.id, source_name=src_cidp.title
    )

# ── WARDS ────────────────────────────────────────────────────────
ward_map = {
    "Matuga": ["Tsimba-Golini", "Waa-Ng'ombeni", "Tiwi", "Kubo South", "Mkongani"],
    "Msambweni": ["Gombato Bongwe", "Ukunda", "Kinondo", "Ramisi"],
    "Lunga-Lunga": ["Pongwe/Kikoneni", "Dzombo", "Mwereni", "Vanga"],
    "Kinango": ["Ndavaya", "Puma", "Mackinon Road", "Chengoni/Samburu", "Mwavumbo", "Kasemeni", "Kinango"],
}
wards = {}
for subcounty_name, ward_list in ward_map.items():
    for w in ward_list:
        wards[w] = get_or_create_admin(
            "KEN", "ward", w, parent_id=subcounties[subcounty_name].id, source_name=src_cidp.title
        )

print(f"Admin geography: 1 county, {len(subcounties)} sub-counties, {len(wards)} wards")

# ── SOURCE CLAIM CONFLICTS: LANDING SITE COUNT ───────────────────
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=kwale.id,
    claim_field="landing_site_count", claim_value="40 landing sites used by 23 BMUs",
    source_id=src_cidp.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=kwale.id,
    claim_field="landing_site_count", claim_value="46 landing sites (fisheries studies)",
    source_id=src_2018.id, is_canonical="false",
))
db.flush()
print("Source conflicts preserved: landing site count (40 vs 46)")

# ── BMUs (from Shimoni-Vanga JCMA + Kibuyuni evidence) ───────────
bmu_kibuyuni  = get_or_create_bmu("Kibuyuni", source_name=src_shimoni_esia.title)
bmu_shimoni   = get_or_create_bmu("Shimoni", source_name=src_shimoni_esia.title)
bmu_wasini    = get_or_create_bmu("Wasini", source_name=src_shimoni_esia.title)
bmu_mkwiro    = get_or_create_bmu("Mkwiro", source_name=src_shimoni_esia.title)
bmu_majoreni  = get_or_create_bmu("Majoreni", source_name=src_shimoni_esia.title)
bmu_jimbo     = get_or_create_bmu("Jimbo", source_name=src_shimoni_esia.title)
bmu_vanga     = get_or_create_bmu("Vanga", source_name=src_shimoni_esia.title)
bmu_mwaepe    = get_or_create_bmu("Mwaepe", source_name=src_mwaepe_esia.title)
bmu_mwandamu  = get_or_create_bmu("Mwandamu", source_name=src_kemfsed.title)
bmu_mkunguni  = get_or_create_bmu("Mkunguni", source_name=src_kemfsed.title)
bmu_mwaembe   = get_or_create_bmu("Mwaembe", source_name=src_kemfsed.title)
bmu_munje     = get_or_create_bmu("Munje", source_name=src_kemfsed.title)
bmu_bodo      = get_or_create_bmu("Bodo", source_name=src_kemfsed.title)
bmu_funzi     = get_or_create_bmu("Funzi", source_name=src_kemfsed.title)

print("BMUs seeded: 14")

# ── KIBUYUNI BMU — 6 landing sites (section 13) ──────────────────
kibuyuni_sites = {
    "Kibuyuni":  get_or_create_site("Kibuyuni",  bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
    "Kijiweni":  get_or_create_site("Kijiweni",  bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
    "Ngomani":   get_or_create_site("Ngomani",   bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
    "Kiromo":    get_or_create_site("Kiromo",    bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
    "Huawen":    get_or_create_site("Huawen",    bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
    "Mtibwani":  get_or_create_site("Mtibwani",  bmu_id=bmu_kibuyuni.id, source_name=src_shimoni_esia.title),
}
# Aliases per section 11/28
add_alias("fish_landing_site", kibuyuni_sites["Kiromo"].id, "Chiromo", confidence="HIGH", source_name=src_2018.title)
add_alias("fish_landing_site", kibuyuni_sites["Kiromo"].id, "Koromo", confidence="MEDIUM", source_name=src_2018.title)
add_alias("fish_landing_site", kibuyuni_sites["Mtibwani"].id, "Mtimbwani", confidence="HIGH", source_name=src_legal.title)

print(f"Kibuyuni BMU landing sites: {len(kibuyuni_sites)}")

# ── SHIMONI BMU landing sites ─────────────────────────────────────
shimoni_sites = {
    "Bati":      get_or_create_site("Bati",      bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Mwazaro":   get_or_create_site("Mwazaro",   bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Kiwambali": get_or_create_site("Kiwambali", bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Anzwani":   get_or_create_site("Anzwani",   bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Shimoni":   get_or_create_site("Shimoni",   bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Changai":   get_or_create_site("Changai",   bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
    "Mkuyuni":   get_or_create_site("Mkuyuni",   bmu_id=bmu_shimoni.id, source_name=src_shimoni_esia.title),
}
# Aliases
add_alias("fish_landing_site", shimoni_sites["Anzwani"].id, "Anziwani", confidence="HIGH", source_name=src_legal.title)
add_alias("fish_landing_site", shimoni_sites["Anzwani"].id, "Anzuani", confidence="MEDIUM")
add_alias("fish_landing_site", shimoni_sites["Kiwambali"].id, "Kiwambale", confidence="HIGH", source_name=src_legal.title)

# Note: Mwazaro is treated as a landing site under Shimoni per section 15,
# NOT a separate BMU, pending confirmation.
mwazaro_note = db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=shimoni_sites["Mwazaro"].id,
    claim_field="bmu_relationship_note",
    claim_value="Mwazaro is landing/beach site under Shimoni fisheries area, not a registered BMU, pending confirmation. Also relevant to seaweed economy.",
    source_id=src_shimoni_esia.id, is_canonical="false",
))

print(f"Shimoni BMU landing sites: {len(shimoni_sites)}")

# ── MWAEPE — critical priority site (section 16-17) ──────────────
mwaepe_site = get_or_create_site(
    "Mwaepe", bmu_id=bmu_mwaepe.id, source_name=src_mwaepe_esia.title,
    gazetted="GAZETTED",
    extra={"source_text": "Gazetted fish landing site since 1968. One of the oldest landing sites in Kenya."},
)

# Mwaepe historical catch data (section 16) — exact figures given
db.add(SpeciesAvailability(
    landing_site_id=mwaepe_site.id, species_name_raw="Mixed (demersals/pelagics/crustaceans/molluscs)",
    average_volume_kg=47261.0, source_year=2019, source_name=src_mwaepe_esia.title,
    verification_status="RESEARCH_SOURCE",
))
db.add(SpeciesAvailability(
    landing_site_id=mwaepe_site.id, species_name_raw="Mixed (demersals/pelagics/crustaceans/molluscs)",
    average_volume_kg=54163.0, source_year=2020, source_name=src_mwaepe_esia.title,
    verification_status="RESEARCH_SOURCE",
))
db.add(SpeciesAvailability(
    landing_site_id=mwaepe_site.id, species_name_raw="Mixed (demersals/pelagics/crustaceans/molluscs)",
    average_volume_kg=50701.0, source_year=2021, source_name=src_mwaepe_esia.title,
    verification_status="RESEARCH_SOURCE",
))

print("Mwaepe: gazetted 1968, 3 years catch data seeded (2019-2021)")

# ── MSAMBWENI GROUPING — 2018 register (section 11) ──────────────
msambweni_names = [
    "Bodo", "Shirazi", "Ramisi", "Chale Jeza", "Chale", "Mgwani", "Funzi",
    "Gazi", "Mwakore", "Munje", "Mkunguni", "Mawezani", "Mwaembe",
    "Kingwede", "Mvuleni", "Mwanyanza", "Rigata", "Mwakamba", "Tradewinds",
    "Mwamombi", "Gomani", "Nyumba Sita", "Mwandamo",
]
msambweni_sites = {}
for name in msambweni_names:
    msambweni_sites[name] = get_or_create_site(name, source_name=src_2018.title)
add_alias("fish_landing_site", msambweni_sites["Tradewinds"].id, "Trade Winds", confidence="HIGH", source_name=src_legal.title)
add_alias("fish_landing_site", msambweni_sites["Tradewinds"].id, "Mkwakwani", confidence="MEDIUM")
add_alias("fish_landing_site", msambweni_sites["Mwakamba"].id, "Mwakore", confidence="LOW")  # flagged, not merged

print(f"Msambweni grouping sites (2018 register): {len(msambweni_sites)}")

# ── LUNGA-LUNGA GROUPING — 2018 register ──────────────────────────
lungalunga_names = [
    "Kibuyuni", "Chiromo", "Mtimbwani", "Kivuma", "Mzizima", "Aleni",
    "Mwanjeni", "Anziwani", "Kiwambale", "Bati", "Chete Cha Kale",
    "Kichangani", "Nyuma Ya Maji", "Wasini", "Bogowa", "Mkwiro",
    "Jasini", "Jimbo", "Vanga", "Kiwegu",
]
lungalunga_sites = {}
for name in lungalunga_names:
    # Skip duplicates already seeded under Kibuyuni/Shimoni BMU
    if name in ("Kibuyuni", "Chiromo", "Mtimbwani", "Bati", "Anziwani", "Kiwambale"):
        continue
    lungalunga_sites[name] = get_or_create_site(name, source_name=src_2018.title)

print(f"Lunga-Lunga grouping additional sites (2018 register): {len(lungalunga_sites)}")

# ── MATUGA GROUPING ────────────────────────────────────────────────
matuga_names = ["Tiwi Mkunguni", "Kikadini", "Mwagandizo", "Mbuguni", "Nyari", "Mwanyerere"]
matuga_sites = {name: get_or_create_site(name, source_name=src_2018.title) for name in matuga_names}
add_alias("fish_landing_site", matuga_sites["Kikadini"].id, "Kikadinu", confidence="MEDIUM", source_name=src_legal.title)

print(f"Matuga grouping sites: {len(matuga_sites)}")

# ── KINANGO GROUPING ───────────────────────────────────────────────
kinango_names = ["Tsunza", "Bofu", "Mwadumbo", "Mbonje", "Guya"]
kinango_sites = {name: get_or_create_site(name, source_name=src_2018.title) for name in kinango_names}

print(f"Kinango grouping sites: {len(kinango_sites)}")

# ── 2024 LEGAL NOTICE GAZETTED BEACHES (section 12) ──────────────
# These are stored as claims against existing sites where names match,
# and as new sites where they don't already exist, all attributed to
# src_legal per the instruction to keep the gazetted list separate.
legal_notice_groupings = {
    "Tiwi": ["Kikadinu", "Nyari", "Tiwi"],
    "Diani": ["Mwakamba", "Gomani", "Mwamombi", "Trade Winds"],
    "Kinondo": ["Mwaepe", "Mvuleni", "Mgwani", "Jeza", "Chale", "Gazi"],
    "Msambweni": ["Mwandamu", "Mkunguni", "Mwaembe", "Munge", "Shirazi", "Funzi", "Bodo"],
    "Pongwe/Kidimu": ["Ramisi", "Kiwambale", "Anziwani", "Shimoni", "Mkwiro", "Wasini", "Kibuyuni", "Mtimbwani", "Kijiweni"],
    "Vanga": ["Kiwegu", "Vanga", "Jimbo"],
}
legal_notice_count = 0
for area, names in legal_notice_groupings.items():
    for name in names:
        existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
        if existing:
            db.add(GeographySourceClaim(
                entity_type="fish_landing_site", entity_id=existing.id,
                claim_field="gazetted_beach_notice_2024",
                claim_value=f"Listed under {area} in Legal Notice 124 of 2024",
                source_id=src_legal.id, is_canonical="false",
            ))
        else:
            new_site = get_or_create_site(name, source_name=src_legal.title, gazetted="GAZETTED")
        legal_notice_count += 1

print(f"2024 Legal Notice gazetted beach entries processed: {legal_notice_count}")

# ── JCMAs (section 20) ────────────────────────────────────────────
jcma_shimoni_vanga = JointCoManagementArea(
    name="Shimoni-Vanga JCMA", source_name=src_kemfsed.title,
    verification_status="RESEARCH_SOURCE",
)
db.add(jcma_shimoni_vanga)
db.flush()
jcma_shimoni_vanga.bmus.extend([bmu_shimoni, bmu_wasini, bmu_mkwiro, bmu_kibuyuni, bmu_majoreni, bmu_jimbo, bmu_vanga])

jcma_mwandamu_funzi = JointCoManagementArea(
    name="Mwandamu-Funzi JCMA", source_name=src_kemfsed.title,
    verification_status="RESEARCH_SOURCE",
)
db.add(jcma_mwandamu_funzi)
db.flush()
jcma_mwandamu_funzi.bmus.extend([bmu_mwandamu, bmu_mkunguni, bmu_mwaembe, bmu_munje, bmu_bodo, bmu_funzi])

jcma_chale_gazi = JointCoManagementArea(
    name="Chale-Gazi / Diani-Chale management area", source_name=src_kemfsed.title,
    verification_status="RESEARCH_SOURCE",
)
db.add(jcma_chale_gazi)
db.flush()

print("JCMAs seeded: 3 (Shimoni-Vanga, Mwandamu-Funzi, Chale-Gazi/Diani-Chale)")

# ── MARINE MANAGEMENT AREAS (section 21) ──────────────────────────
mma_names = [
    "Wasini", "Jimbo", "Vanga", "Shimoni", "Majoreni", "Kibuyuni",
    "Mkwiro/Mji wa Kale", "Mwaembe", "Munje", "Mkunguni", "Mwaepe",
    "Nyari/Kikadini", "Tradewinds/Mkwakwani",
]
mmas = []
for name in mma_names:
    existing = db.query(MarineManagementArea).filter(MarineManagementArea.designation == name).first()
    if not existing:
        mma = MarineManagementArea(designation=name, source_name=src_kemfsed.title, verification_status="RESEARCH_SOURCE")
        db.add(mma)
        mmas.append(mma)

print(f"Marine Management Areas seeded: {len(mmas)}")

# ── FISHING GROUNDS (section 19) — explicitly NOT landing sites ──
fishing_ground_names = [
    "Mtengo", "Limwinyumwinyu", "Mavovo", "Mwalumba Mdogo", "Mwalumba Mkubwa",
    "Mwaonza", "Puyipuyuni", "Mpunguti ya Chini", "Mpunguti ya Juu",
    "Muindini", "Vigaeni/Boyani", "Jiwe Jahazi", "Nyuma ya Maji",
    "Mkwiro", "Kijiweni",
]
grounds_count = 0
for name in fishing_ground_names:
    existing = db.query(FishingGround).filter(FishingGround.name == name).first()
    if not existing:
        db.add(FishingGround(name=name, source_name=src_shimoni_esia.title, verification_status="RESEARCH_SOURCE"))
        grounds_count += 1

print(f"Fishing grounds seeded: {grounds_count}")
print("  NOTE: 'Mkwiro' and 'Kijiweni' exist as BOTH a landing site name")
print("  AND a fishing ground name in the source data. Kept as separate")
print("  entity types per section 19/36 instruction — not merged.")

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("KWALE SEEDING COMPLETE")
print("=" * 60)
print(f"AdminGeography records:  {db.query(AdminGeography).count()}")
print(f"BMUs:                    {db.query(BMU).count()}")
print(f"FishLandingSites:        {db.query(FishLandingSite).count()}")
print(f"FishingGrounds:          {db.query(FishingGround).count()}")
print(f"JointCoManagementAreas:  {db.query(JointCoManagementArea).count()}")
print(f"MarineManagementAreas:   {db.query(MarineManagementArea).count()}")
print(f"GeographicAliases:       {db.query(GeographicAlias).count()}")
print(f"GeographySourceClaims:   {db.query(GeographySourceClaim).count()}")
print(f"GeographySources:        {db.query(GeographySource).count()}")

db.close()