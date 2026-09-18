# scripts/seed_zanzibar_pemba_phase1.py
#
# Zanzibar / Pemba Phase 1 seed — Tiers A/B/C. Pemba carries the
# richer governance dataset (SFCs, CMGs, PECCA structure) so this
# script is substantially larger than the Unguja one, correctly
# reflecting the source material rather than artificially balancing
# the two.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.comanagement import MarineManagementArea, JointCoManagementArea
from app.models.intelligence.shehia_fisheries_committee import ShehiaFisheriesCommittee
from app.models.intelligence.management_area import ManagementArea

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


def get_or_create_site(name, village=None, source_name=None, vessel_count=None,
                        registered_fishers=None, data_stage="survey_identified",
                        classification=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    s = FishLandingSite(
        official_name=name, local_name=village, source_name=source_name,
        verification_status="RESEARCH_SOURCE", data_verification_stage=data_stage,
        estimated_boat_count=vessel_count,
        estimated_fisher_count=registered_fishers,
        site_classification=classification, production_system="wild_capture",
    )
    db.add(s)
    db.flush()
    return s


def get_or_create_sfc(name, source_name=None, affiliation_status="unknown"):
    existing = db.query(ShehiaFisheriesCommittee).filter(ShehiaFisheriesCommittee.name == name).first()
    if existing:
        return existing
    sfc = ShehiaFisheriesCommittee(
        name=name, source_name=source_name, verification_status="RESEARCH_SOURCE",
        cmg_affiliation_status=affiliation_status,
    )
    db.add(sfc)
    db.flush()
    return sfc


print("=" * 60)
print("SEEDING ZANZIBAR / PEMBA — PHASE 1")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_jica2024 = get_or_create_source("JICA Fisheries Sector Survey (reporting 2020 Zanzibar Frame Survey)", org="JICA", year=2024, doc_type="Frame survey / sector report", tier=1)
src_pecca2026 = get_or_create_source("Peer-reviewed PECCA study (Pemba Channel Conservation Area)", year=2026, doc_type="Peer-reviewed study", tier=1)
src_mwambao = get_or_create_source("Mwambao Coastal Community Network — CMG documentation", doc_type="NGO governance documentation", tier=2)
src_blue_alliance = get_or_create_source("Blue Alliance participatory mapping and fisheries-management reports", doc_type="NGO field documentation", tier=2)
src_governance_study = get_or_create_source("Peer-reviewed study of community fisheries governance (Pemba SFC sample)", doc_type="Peer-reviewed journal article", tier=1)
src_unep2026 = get_or_create_source("UNEP-linked description of PECCA management areas", org="UNEP", year=2026, doc_type="Institutional report", tier=1)
src_older_sfc_count = get_or_create_source("Older political/programme documentation citing ~91 fisheries committees", doc_type="Secondary/programme document", tier=4)

print("Sources seeded: 7")

# ── ADMIN GEOGRAPHY — Zanzibar > Pemba > Region > District ──────────
zanzibar = get_or_create_admin("TZA", "semi_autonomous_region", "Zanzibar")
pemba    = get_or_create_admin("TZA", "island", "Pemba", parent_id=zanzibar.id, source_name=src_jica2024.title)

pemba_regions = {
    "Kaskazini Pemba": get_or_create_admin("TZA", "region", "Kaskazini Pemba", parent_id=pemba.id),
    "Kusini Pemba":     get_or_create_admin("TZA", "region", "Kusini Pemba", parent_id=pemba.id),
}
pemba_district_map = {
    "Kaskazini Pemba": ["Micheweni", "Wete"],
    "Kusini Pemba":     ["Chake Chake", "Mkoani"],
}
pemba_districts = {}
for region_name, district_list in pemba_district_map.items():
    for d in district_list:
        pemba_districts[d] = get_or_create_admin("TZA", "district", d, parent_id=pemba_regions[region_name].id)

print(f"Admin geography: Zanzibar > Pemba > {len(pemba_regions)} regions > {len(pemba_districts)} districts")

# ── LANDING SITE COUNT CONFLICTS ────────────────────────────────────
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=pemba.id,
    claim_field="landing_site_count",
    claim_value="126 Pemba landing sites of 235 total (2020 Zanzibar Frame Survey) — 54% of total despite Unguja having the stronger tourism economy",
    source_id=src_jica2024.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=pemba.id,
    claim_field="landing_site_count",
    claim_value="11 Pemba sites field-confirmed during JICA field verification (of 126 identified)",
    source_id=src_jica2024.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=pemba.id,
    claim_field="landings_volume_2020",
    claim_value="Pemba: ~14,987 tonnes (2020, JICA estimate) vs Unguja ~23,119 tonnes; Pemba→Unguja inter-island seafood movement documented, ~100 tonnes recorded June-Nov 2023, ~200 tonnes/year estimated on recorded basis — future SupplyCorridor candidate",
    source_id=src_jica2024.id, is_canonical="false",
))

# ── TIER A — 13 high-vessel Pemba landing sites ─────────────────────
pemba_high_vessel = [
    ("Mitepeni",       "Tumbe Mashariki",   167),
    ("Pambwarahaji",   "Tumbe Magharibi",   152),
    ("Mpene Bwegeza",  "Mwambe",            141),
    ("Kwa Makame",     "Kwanja Shamiani",    95),
    ("Kwamjariwi",     "Shumba Mjini",       95),
    ("Misufini",       "Kiwani",             82),
    ("Kiwijini",       "Kibaridi",           60),
    ("Mtangani",       "Mtangani",           59),
    ("Chole",          "Chole",              55),
    ("Kifumkwe",       "Chokocho",           53),
    ("Mkwajuni",       "Fundo",              50),
    ("Tapni",          "Msuka",              49),
    ("Kenya",          "Gando",              43),
]
site_count = 0
for name, village, vessels in pemba_high_vessel:
    get_or_create_site(name, village=village, source_name=src_jica2024.title,
                        vessel_count=vessels, data_stage="confirmed",
                        classification="HIGH_VESSEL_SITE")
    site_count += 1
print(f"Tier A — high-vessel Pemba sites seeded: {site_count}")

# ── TIER A — 4 JICA priority sites (Pemba) ──────────────────────────
priority_sites_pemba = ["Shumba Mjini", "Tumbe Mashariki", "Wete Pwani", "Wesha"]
for name in priority_sites_pemba:
    s = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if not s:
        s = get_or_create_site(name, source_name=src_jica2024.title, data_stage="confirmed")
    s.site_classification = (s.site_classification or "") + ",JICA_PRIORITY_SITE,DETAILED_ASSESSMENT"
db.flush()
print(f"Tier A — JICA priority Pemba sites tagged: {len(priority_sites_pemba)}")

# ── TIER A — PECCA registered-fisher landing sites (cross-corroborated) ──
pecca_sites = {
    "Mkoani Pwani":       265,
    "Wesha":               282,  # corroborates JICA priority site above
    "Wete Pwani":          398,  # corroborates JICA priority site above
    "Makangale Ulingoni":  539,
}
for name, fishers in pecca_sites.items():
    s = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if not s:
        s = get_or_create_site(name, source_name=src_pecca2026.title,
                                registered_fishers=fishers, data_stage="confirmed")
    else:
        s.estimated_fisher_count = fishers
        if name in ("Wesha", "Wete Pwani"):
            db.add(GeographySourceClaim(
                entity_type="fish_landing_site", entity_id=s.id,
                claim_field="cross_source_corroboration",
                claim_value=f"Also documented as JICA priority site — registered fisher count ({fishers}) from independent PECCA 2026 study, strengthening confidence",
                source_id=src_pecca2026.id, is_canonical="false",
            ))
db.flush()
print(f"PECCA registered-fisher sites seeded/updated: {len(pecca_sites)}")

db.add(GeographySourceClaim(
    entity_type="marine_management_area", entity_id=None,
    claim_field="pecca_scale",
    claim_value="PECCA covers ~1,000 km² along Pemba's western coastline, containing 72 landing sites, supporting ~11,328 artisanal fishers (Dept. of Fisheries Development data, per 2026 peer-reviewed study). Only 4 of 72 landing sites individually seeded this phase.",
    source_id=src_pecca2026.id, is_canonical="false",
))

# ── TIER A — PECCA management areas (partial — Tier D acknowledged) ──
pecca_mca = db.query(MarineManagementArea).filter(MarineManagementArea.designation == "Pemba Channel Conservation Area").first()
mgmt_areas = {}
if pecca_mca:
    for zone_name, zone_num in [("PECCA Zone 5", "5"), ("PECCA Zone 6", "6"), ("PECCA Management Area No. 3", "3")]:
        existing = db.query(ManagementArea).filter(ManagementArea.name == zone_name).first()
        if not existing:
            ma = ManagementArea(
                name=zone_name, marine_management_area_id=pecca_mca.id, zone_number=zone_num,
                source_name=src_unep2026.title, verification_status="RESEARCH_SOURCE",
            )
            db.add(ma)
            db.flush()
            mgmt_areas[zone_name] = ma
        else:
            mgmt_areas[zone_name] = existing
    db.add(GeographySourceClaim(
        entity_type="marine_management_area", entity_id=pecca_mca.id,
        claim_field="management_area_count",
        claim_value="UNEP-linked 2026 source states 6 total PECCA management areas exist; only Zone 5, Zone 6, and 'Management Area No. 3' are individually named/documented. Remaining ~3 NOT seeded — explicit gap, not invented.",
        source_id=src_unep2026.id, is_canonical="false",
    ))
print(f"PECCA management areas seeded: {len(mgmt_areas)} of stated 6 total (gap explicitly recorded)")

# ── TIER B — documented SFCs, with provenance, NOT a complete registry ──
sfc_names_confirmed = [
    "Mtambwe North", "Selemu", "Gando", "Fundo", "Ukunjwi",
    "Stahabu", "Michenzani", "Shidi", "Makoongwe",
    "Kukuu", "Kangani", "Chokocho", "Kisiwa Panza",
]
sfc_names_unaffiliated = [
    "Mtambwe South", "Kisiwani", "Ndagoni", "Kwale Kichuuni",
    "Ziwani", "Mbuyuni", "Shamiani",
]
sfc_names_recent = ["Makangale", "Tondooni", "Msuka", "Kifundi"]

sfcs = {}
for name in sfc_names_confirmed:
    sfcs[name] = get_or_create_sfc(name, source_name=src_mwambao.title, affiliation_status="affiliated")
for name in sfc_names_unaffiliated:
    sfcs[name] = get_or_create_sfc(name, source_name=src_governance_study.title, affiliation_status="unaffiliated_confirmed")
for name in sfc_names_recent:
    sfcs[name] = get_or_create_sfc(name, source_name=src_blue_alliance.title, affiliation_status="unknown")

db.flush()
print(f"Tier B — SFCs seeded: {len(sfcs)} (confirmed-affiliated: {len(sfc_names_confirmed)}, confirmed-unaffiliated: {len(sfc_names_unaffiliated)}, recent/unclear: {len(sfc_names_recent)})")

db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=pemba.id,
    claim_field="sfc_total_count",
    claim_value="Older secondary sources cite ~91 fisheries committees (58 Unguja + 33 Pemba) — NOT seeded as current count. No authoritative current SFC registry found. Recorded as claim only.",
    source_id=src_older_sfc_count.id, is_canonical="false",
))

# Link Zone 6 SFCs to their ManagementArea (documented overlap)
if "PECCA Zone 6" in mgmt_areas:
    zone6_sfcs = ["Makangale", "Tondooni", "Fundo", "Gando", "Msuka"]
    for name in zone6_sfcs:
        if name in sfcs and sfcs[name] not in mgmt_areas["PECCA Zone 6"].sfcs:
            mgmt_areas["PECCA Zone 6"].sfcs.append(sfcs[name])
    db.flush()
    print(f"PECCA Zone 6 <-> SFC links: {len(zone6_sfcs)} (note: Fundo/Gando names also appear in MSEGAFU CMG context — same or distinct entities not yet resolved)")

# ── TIER C — CMGs with documented (evolving) membership ─────────────
cmg_data = [
    ("MSEGAFU",    2019, ["Mtambwe North", "Selemu", "Gando", "Fundo", "Ukunjwi"], "original"),
    ("STAMISHIMA", 2019, ["Stahabu", "Michenzani", "Shidi", "Makoongwe"], "original — first documented CMG"),
    ("KUKACHOKI",  None, ["Kukuu", "Kangani", "Chokocho", "Kisiwa Panza"], "original"),
]
cmg_count = 0
for cmg_name, formed_year, member_names, note in cmg_data:
    existing_cmg = db.query(JointCoManagementArea).filter(JointCoManagementArea.name == cmg_name).first()
    if not existing_cmg:
        cmg = JointCoManagementArea(
            name=cmg_name, source_name=src_mwambao.title, verification_status="VERIFIED_SECONDARY",
            governance_type="CMG",
            description=f"Formed {formed_year or 'year unconfirmed'}. {note}. Membership per {src_mwambao.title}.",
        )
        db.add(cmg)
        db.flush()
        for member_name in member_names:
            if member_name in sfcs:
                sfcs[member_name].cmgs.append(cmg)
        cmg_count += 1
db.flush()

# 2025 update — different/evolved membership for existing CMG names, preserved as separate claim
db.add(GeographySourceClaim(
    entity_type="jcm_as", entity_id=None,
    claim_field="cmg_membership_2025_update",
    claim_value="2025 Mwambao update lists 4 CMG offices with different/narrower membership than 2019 documentation: PEDIM5 (Muyuni), MMKIJO (Mtowapwani), KUKACHOKI (Kangani only), MSEGAFU (Ukunjwi only). NOT merged with original 2019 membership — recorded as evolution, not replacement, since CMGs are an evolving operational layer, not a static administrative unit.",
    source_id=src_mwambao.id, is_canonical="false",
))
print(f"Tier C — CMGs seeded: {cmg_count} (MSEGAFU, STAMISHIMA, KUKACHOKI) with 2019-era membership; 2025 evolution recorded as separate claim, not merged")

db.add(GeographySourceClaim(
    entity_type="jcm_as", entity_id=None,
    claim_field="research_gap",
    claim_value="Mwambao reports helping establish 7 CMGs total in Zanzibar — only 3 (2019-era) + partial 2025 update (4 named offices) documented here. Full current CMG registry not recovered. New 2026 'CMA' vocabulary (T4K, KIFUMAKI, KIFUPIMUPO, northeast Unguja) NOT seeded this phase — recorded as a distinct emerging governance concept, deliberately not collapsed into CMG.",
    source_id=src_blue_alliance.id, is_canonical="false",
))

db.commit()

print()
print("=" * 60)
print("ZANZIBAR / PEMBA PHASE 1 COMPLETE")
print("=" * 60)
print(f"FishLandingSites (Pemba, this script): {site_count} high-vessel + {len(pecca_sites)} PECCA-fisher sites")
print(f"ShehiaFisheriesCommittees: {len(sfcs)}")
print(f"CollaborativeManagementGroups (JointCoManagementArea, governance_type=CMG): {cmg_count}")
print(f"ManagementAreas (PECCA sub-zones): {len(mgmt_areas)} of stated 6")
print("Tier D gaps explicitly recorded: full SFC registry, full CMG registry, complete 235-site names, CMA boundaries")

db.close()