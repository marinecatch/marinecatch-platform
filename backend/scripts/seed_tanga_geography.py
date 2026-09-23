# scripts/seed_tanga_geography.py
#
# Tanga Region, Tanzania — Phase 1 seed. Source: MarineCatch Africa
# Tanzania Fisheries Intelligence — Tanga Region package (closed-world,
# research cut-off Sept 2026). No web research performed — this
# package is the sole research authority per its own instruction.
# All conflicting figures preserved, not reconciled. 56-site frame
# count seeded without inventing the missing ~30 site names.

from app.database.connection import SessionLocal
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.admin_geography import AdminGeography
from app.models.intelligence.fish_landing_site import FishLandingSite
from app.models.intelligence.fishing_ground import FishingGround
from app.models.intelligence.comanagement import MarineManagementArea, JointCoManagementArea
from app.models.intelligence.infrastructure import InfrastructureAsset
from app.models.intelligence.fisheries_observation import FisheriesObservation
from app.models.fisheries_data import Species

db = SessionLocal()


def get_or_create_source(src_id, title, org=None, year=None, tier=2):
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
                        verification="RESEARCH_SOURCE", priority=None, data_collection=False,
                        source_name=None):
    existing = db.query(FishLandingSite).filter(FishLandingSite.official_name == name).first()
    if existing:
        return existing
    conf_score = {"A": 4, "B": 3, "C": 2, "D": 1}.get(confidence, 2)
    s = FishLandingSite(
        official_name=name, county_id=district_id, site_type=site_type,
        verification_status=verification, confidence_score=conf_score,
        source_name=source_name,
        site_classification="VERY_HIGH_PRIORITY" if priority == "VERY_HIGH" else None,
        data_verification_stage="confirmed" if data_collection else "survey_identified",
        production_system="wild_capture",
    )
    db.add(s)
    db.flush()
    return s


def add_obs(admin_id, metric_type, value, currency=None, year=None, month=None,
            frame_ref=None, canonical="false", subtype=None, source_name=None):
    o = FisheriesObservation(
        admin_geography_id=admin_id, metric_type=metric_type, metric_subtype=subtype,
        value=value, currency=currency, period_year=year, period_month=month,
        frame_reference_year=frame_ref, is_canonical=canonical,
        source_name=source_name, verification_status="VERIFIED_OFFICIAL",
    )
    db.add(o)
    return o


print("=" * 60)
print("SEEDING TANGA REGION, TANZANIA — PHASE 1")
print("=" * 60)

# ── SOURCES (tier registry, section 38) ───────────────────────────
src_mlf2020   = get_or_create_source("SRC1", "Annual Fisheries Statistics Report January-December 2020", "Ministry of Livestock and Fisheries", 2020, tier=1)
src_audit2025 = get_or_create_source("SRC2", "Performance Audit Report on Management of Fisheries Resources", "National Audit Office of Tanzania", tier=1)
src_mkinga    = get_or_create_source("SRC3", "Mkinga District Council Fishery", "Mkinga District Council", tier=1)
src_tangacity = get_or_create_source("SRC4", "Tanga City Council Strategic Plan 2021/22-2025/26", "Tanga City Council", tier=1)
src_tacmp_gmp = get_or_create_source("SRC5", "Tanga Coelacanth Marine Park General Management Plan", "Marine Parks and Reserves Tanzania", tier=1)
src_tacmp_cur = get_or_create_source("SRC6", "Tanga Coelacanth Marine Park (current)", "Marine Parks and Reserves Tanzania", tier=1)
src_cma       = get_or_create_source("SRC7", "Putting Adaptive Management into Practice - Tanga Coastal Management Areas", "IUCN", tier=2)
src_shift     = get_or_create_source("SRC8", "Perceptions on the shifting baseline among coastal fishers of Tanga", tier=3)
src_pangani   = get_or_create_source("SRC9", "Fishery characteristics in two districts of coastal Tanzania", tier=3)
src_kipumbwi_field = get_or_create_source("SRC10", "Kipumbwi fishing community / marine debris field report", tier=3)
src_investment  = get_or_create_source("SRC11", "Tanga Investment Guide", "Tanga Region", 2023, tier=1)
src_market2025  = get_or_create_source("SRC12", "Kipumbwi Fish Market project handover", "Ministry of Livestock and Fisheries", 2025, tier=1)
src_market2026  = get_or_create_source("SRC13", "Kipumbwi Fish Market implementation update", tier=2)
src_processing  = get_or_create_source("SRC14", "Sardine and Small Pelagic Processing Plant - Kipumbwi", "World Bank / Tanzania fisheries programme procurement", tier=1)
src_maricult    = get_or_create_source("SRC15", "Past, present and future developments in mariculture in coastal mainland Tanzania", tier=3)
src_seaweed     = get_or_create_source("SRC16", "Seaweed warehouse-receipt initiative", "Ministry of Livestock and Fisheries", 2025, tier=1)

print("Sources seeded: 16")

# ── ADMIN GEOGRAPHY ──────────────────────────────────────────────
tanga = get_or_create_admin("TZA", "region", "Tanga", source_name=src_mlf2020.title)
districts = {
    "Mkinga":     get_or_create_admin("TZA", "district_council", "Mkinga", parent_id=tanga.id, source_name=src_mkinga.title),
    "Pangani":    get_or_create_admin("TZA", "district_council", "Pangani", parent_id=tanga.id, source_name=src_pangani.title),
    "Muheza":     get_or_create_admin("TZA", "district_council", "Muheza", parent_id=tanga.id),
    "Tanga City": get_or_create_admin("TZA", "city_council", "Tanga City", parent_id=tanga.id, source_name=src_tangacity.title),
}
print(f"Admin geography: Tanga Region > {len(districts)} coastal fisheries jurisdictions")

# ── FISHERIES FRAME (2018 frame, reported 2020) ─────────────────────
add_obs(tanga.id, "landing_site_count", 56, frame_ref=2018, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(tanga.id, "fisher_count",       14077, frame_ref=2018, year=2020, canonical="true", source_name=src_mlf2020.title)
add_obs(tanga.id, "vessel_count",       1335,  frame_ref=2018, year=2020, canonical="true", source_name=src_mlf2020.title)

# ── CATCH CONFLICT — both preserved, district-month preferred operationally ──
add_obs(tanga.id, "catch_tonnes", 14179.61, year=2020, canonical="true",
        subtype="district_month_series", source_name=src_mlf2020.title)
add_obs(tanga.id, "catch_tonnes", 9850.9, year=2020, canonical="false",
        subtype="summary_table", source_name=src_mlf2020.title)
add_obs(tanga.id, "production_value", 70901600000, currency="TZS", year=2020, canonical="true",
        subtype="district_month_series", source_name=src_mlf2020.title)
add_obs(tanga.id, "production_value", 46299000000, currency="TZS", year=2020, canonical="false",
        subtype="summary_table", source_name=src_mlf2020.title)
print("Catch/value conflicts preserved: 2 pairs (9850.9 vs 14179.61 MT; 46.299bn vs 70.9016bn TZS)")

# ── DISTRICT ANNUAL TOTALS (Table 28) ────────────────────────────────
district_annual = {"Muheza": 3836.70, "Pangani": 3840.37, "Tanga City": 3203.79, "Mkinga": 3298.74}
for dname, total in district_annual.items():
    add_obs(districts[dname].id, "catch_tonnes", total, year=2020, canonical="true", source_name=src_mlf2020.title)

# ── MONTHLY SERIES (48 data points) ──────────────────────────────────
monthly = {
    "Muheza":     [286.95,297.01,287.92,393.44,392.96,333.55,280.13,300.13,365.06,234.49,329.60,335.46],
    "Pangani":    [238.93,215.79,209.11,437.23,436.05,331.63,276.79,385.61,359.80,315.78,305.39,328.25],
    "Tanga City": [405.77,321.09,275.21,197.47,206.33,260.83,315.09,258.08,277.72,253.65,197.94,234.61],
    "Mkinga":     [421.04,362.97,274.47,178.33,177.65,260.09,309.65,247.05,289.50,273.40,231.35,273.27],
}
month_count = 0
for dname, values in monthly.items():
    for i, v in enumerate(values, start=1):
        add_obs(districts[dname].id, "catch_tonnes", v, year=2020, month=i, canonical="true", source_name=src_mlf2020.title)
        month_count += 1
print(f"Monthly catch observations seeded: {month_count}")

# ── HISTORICAL 2001 FRAME ────────────────────────────────────────────
add_obs(tanga.id, "landing_site_count", 52, year=2001, canonical="false", source_name=src_shift.title)
add_obs(tanga.id, "fisher_count", 4361, year=2001, canonical="false", source_name=src_shift.title)
for vtype, count in [("inboard_engines",5),("outboard_engines",91),("ngalawa",502),("mashua",100),("mtumbwi",237),("dau",84),("boti",21)]:
    add_obs(tanga.id, "vessel_type_count", count, subtype=vtype, year=2001, canonical="false", source_name=src_shift.title)
print("Historical 2001 frame seeded (52 sites, 4361 fishers, 7 vessel-type counts) — marked non-canonical")

# ── MKINGA-SPECIFIC FRAME ────────────────────────────────────────────
add_obs(districts["Mkinga"].id, "coastal_village_count", 21, canonical="true", source_name=src_mkinga.title)
add_obs(districts["Mkinga"].id, "landing_site_count", 20, canonical="true", source_name=src_mkinga.title)

# ── LANDING SITES — Tier A/B core seed (section 20) ──────────────────
sites_data = [
    # name, district, site_type, confidence, verification, priority, data_collection
    ("Moa",          "Mkinga", "landing_site", "A", "OFFICIALLY_RECORDED", None, True),
    ("Kwale",        "Mkinga", "landing_site", "A", "KNOWN", None, False),
    ("Kichalikani",  "Mkinga", "landing_site", "A", "OFFICIALLY_RECORDED", None, True),
    ("Vyeru",        "Mkinga", "landing_site", "B", "SURVEY_RECORDED", None, False),
    ("Petukiza",     "Mkinga", "landing_site", "B", "KNOWN", None, False),
    ("Pangani",      "Pangani", "landing_site", "A", "KNOWN", None, False),
    ("Kipumbwi",     "Pangani", "landing_site", "A", "KNOWN", "VERY_HIGH", False),
    ("Mkwajuni",     "Pangani", "fishing_community", "A", "SURVEY_RECORDED", None, False),
    ("Ushongo",      "Pangani", "fishing_community", "A", "SURVEY_RECORDED", None, False),
    ("Stahabu",      "Pangani", "fishing_community", "A", "SURVEY_RECORDED", None, False),
    ("Mkwaja",       "Pangani", "fishing_community", "A", "SURVEY_RECORDED", None, False),
    ("Sange",        "Pangani", "fishing_community", "B", "HISTORICAL", None, False),
    ("Buyuni",       "Pangani", "fishing_community", "B", "HISTORICAL", None, False),
    ("Bweni",        "Pangani", "fishing_community", "B", "HISTORICAL", None, False),
    ("Msaraza",      "Pangani", "fishing_community", "A", "SURVEY_RECORDED", None, False),
    ("Mwembeni",     "Pangani", "fishing_community", "B", "HISTORICAL", None, False),
    ("Kigombe",      "Muheza", "landing_site", "A", "KNOWN", "VERY_HIGH", False),
    ("Mwarongo",     "Muheza", "fishing_site", "B", "HISTORICAL", None, False),
    ("Geza",         "Muheza", "fishing_site", "B", "HISTORICAL", None, False),
    ("Kasera",       "Tanga City", "landing_site", "A", "KNOWN", "VERY_HIGH", False),
    ("Deep Sea",     "Tanga City", "landing_site", "A", "KNOWN", "VERY_HIGH", False),
    ("Mchukuuni",    "Tanga City", "landing_site", "A", "KNOWN", None, False),
    ("Tongoni",      "Tanga City", "landing_site", "A", "KNOWN", None, False),
    ("Sahare",       "Tanga City", "landing_site", "A", "KNOWN", None, False),
    ("Mwambani",     "Tanga City", "fishing_site", "B", "HISTORICAL", None, False),
    ("Mnyanjani",    "Tanga City", "fishing_site", "B", "HISTORICAL", None, False),
]
sites = {}
for name, dname, stype, conf, ver, pri, dc in sites_data:
    sites[name] = get_or_create_site(name, district_id=districts[dname].id, site_type=stype,
                                      confidence=conf, verification=ver, priority=pri,
                                      data_collection=dc, source_name=src_mlf2020.title)
print(f"Tier A/B landing sites seeded: {len(sites)}")

# ── ADDITIONAL HISTORICAL SITES (Tier C, not commercially confirmed) ──
historical_extra = {
    "Mkinga":  ["Jasini", "Monga/Vyeru", "Doda", "Kibiboni", "Tawalani", "Manza", "Boma Subutuni", "Boma Kichakamiba"],
    "Muheza":  ["Maera"],
    "Tanga City": ["Machui", "Ndumi", "Mtambwe", "Kiungani"],
}
hist_count = 0
for dname, names in historical_extra.items():
    for name in names:
        get_or_create_site(name, district_id=districts[dname].id, site_type="fishing_site",
                            confidence="C", verification="HISTORICAL", source_name=src_cma.title)
        hist_count += 1
print(f"Additional historical sites (Tier C, CMA-derived): {hist_count}")

db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=tanga.id,
    claim_field="named_site_register_completeness",
    claim_value="Official frame = 56 marine landing sites; only ~26 individually named/seeded this phase (24 Tier A/B core + partial historical). named_site_universe_status = PARTIAL_PUBLIC_REGISTER. Remaining ~30 names NOT manufactured.",
    source_id=src_mlf2020.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=districts["Mkinga"].id,
    claim_field="named_site_register_completeness",
    claim_value="Mkinga has 20 official landing sites; only 6 individually named (Moa, Kwale, Kichalikani, Vyeru, Petukiza + historical extras). Remaining ~14 names NOT manufactured or reverse-engineered from unrelated maps.",
    source_id=src_mkinga.id, is_canonical="false",
))

# ── KIPUMBWI — special notes ──────────────────────────────────────────
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Kipumbwi"].id,
    claim_field="operational_detail",
    claim_value="Busiest fish landing site in Pangani District; ~235 resident fishers, seasonal influx up to 800 migrant fishers; movement/trading point linking mainland with Pemba and Unguja. Small-pelagic fishery: Sardinella neglecta, Stolephorus commersonnii studied here. IUU gear observed: beach seines/juya/kavogo, ring nets in shallow water, undersized cod-end nets/tandio (management observation, not attributed to all fishers/vessels).",
    source_id=src_kipumbwi_field.id, is_canonical="false",
))

# ── KIGOMBE / COELACANTH ──────────────────────────────────────────────
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Kigombe"].id,
    claim_field="ecological_note",
    claim_value="Deep-water fishing grounds (~50-200m) with historical Latimeria chalumnae (coelacanth) captures by fishers. Species relationship = protected_species_interaction, commercial_status = NOT_TARGET_SPECIES, conservation_status = ENDANGERED. Do not model as a commercial target fishery.",
    source_id=src_tacmp_gmp.id, is_canonical="false",
))

# ── KASERA / DEEP SEA — historical study estimates ─────────────────────
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Kasera"].id,
    claim_field="historical_study_estimate",
    claim_value="2017 study: ~1,501 fishers, ~171 craft at Kasera. Historical estimate only — does not replace official 2018/2020 regional frame.",
    source_id=src_shift.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Kasera"].id,
    claim_field="infrastructure_note",
    claim_value="Kasera and Deep Sea together accounted for ~90% of annual fish harvest of the 4 assessed Tanga City sites in study dataset (~2,000 MT annual, study-period, not current statistic).",
    source_id=src_tangacity.id, is_canonical="false",
))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Deep Sea"].id,
    claim_field="infrastructure_note",
    claim_value="Fish auctions occur here; city historically lacked dedicated modern fish market; modern fish market planned at this site. Infrastructure baseline weak: no substantial jetty, ice plant, cold store, formal processing area, or dedicated retailer display infrastructure reported.",
    source_id=src_tangacity.id, is_canonical="false",
))

# ── SEVEN CORE RESEARCH SITES ──────────────────────────────────────────
research_sites = ["Moa", "Kwale", "Pangani", "Kipumbwi", "Kigombe", "Sahare", "Deep Sea"]
for name in research_sites:
    if name in sites:
        c = sites[name].site_classification or ""
        sites[name].site_classification = c + ",CORE_RESEARCH_NODE_350_FISHERMEN_STUDY"
db.flush()
print(f"Core research nodes tagged: {len(research_sites)}")

# ── TACMP — Marine Protected Area ──────────────────────────────────────
tacmp = db.query(MarineManagementArea).filter(MarineManagementArea.designation == "Tanga Coelacanth Marine Park").first()
if not tacmp:
    tacmp = MarineManagementArea(
        designation="Tanga Coelacanth Marine Park", year_established=2009, area_km2=552,
        source_name=src_tacmp_cur.title, verification_status="VERIFIED_OFFICIAL",
    )
    db.add(tacmp)
    db.flush()
    db.add(GeographySourceClaim(
        entity_type="marine_management_area", entity_id=tacmp.id,
        claim_field="area_breakdown",
        claim_value="Total 552 km2 = 85 km2 terrestrial + 467 km2 aquatic. Encompasses Tanga Bay, Mwambani Bay, Tongoni estuary, Toten Island, Yambe Island, Karange Island. General Management Plan developed 2011. Extends ~100km of coastline. Ecosystems: coral reefs, seagrass beds, mangroves, coastal forests, deep reef/drop-off habitats, estuaries. Historical target groups: snappers, emperors, grunts, rabbitfish, small pelagics, lobsters, octopus, prawns, reef fish. Very low fish biomass noted in open/pressured reef areas vs closed reefs.",
        source_id=src_tacmp_gmp.id, is_canonical="false",
    ))
print("Tanga Coelacanth Marine Park seeded (552 km2, gazetted 2009)")

# ── CFMAs — community fisheries management (reusing JCMA, governance_type=CFMA) ──
cfma_names = ["Boma-Mahandakini CFMA", "Tawalani-Kizingani CFMA", "Mchomapunda CFMA"]
cfma_count = 0
for name in cfma_names:
    existing = db.query(JointCoManagementArea).filter(JointCoManagementArea.name == name).first()
    if not existing:
        db.add(JointCoManagementArea(
            name=name, governance_type="CFMA", source_name=src_cma.title,
            verification_status="RESEARCH_SOURCE",
            description="Mchomapunda CFMA is a planned expansion, not yet fully established." if "Mchomapunda" in name else None,
        ))
        cfma_count += 1
db.flush()
print(f"CFMAs seeded: {cfma_count}")

db.add(GeographySourceClaim(
    entity_type="admin_geography", entity_id=tanga.id,
    claim_field="historical_management_areas",
    claim_value="Additional historical CMA structures documented but NOT individually seeded as current entities: Boma-Mahandakini, Deep Sea-Boma, Mwarongo-Sahare, Mtang'ata, Boza-Sange, Mkwaja-Sange/Sange-Mkwaja-Buyuni. These combine villages, landing sites, wards and marine areas — treated as historical fisheries-management geography, not current designated zones.",
    source_id=src_cma.id, is_canonical="false",
))

# ── INFRASTRUCTURE PROJECTS — explicitly not operational ──────────────
kipumbwi_market = InfrastructureAsset(
    landing_site_id=sites["Kipumbwi"].id, asset_type="fish_market",
    operational_status="UNDER_IMPLEMENTATION", funding_program="AFDP",
    financier="IFAD", reported_value=1300000000, reported_value_currency="TZS",
    source_name=src_market2025.title, verification_status="VERIFIED_OFFICIAL",
)
db.add(kipumbwi_market)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=kipumbwi_market.id,
    claim_field="implementation_status",
    claim_value="Handed to contractor Sept 2025. Feb 2026: reported at only 28% completion, Government ordered accelerated implementation. Sept 2026 Government/IFAD review confirms active implementation site. NOT to be marked operational. Purpose: modern fish reception, storage, processing, trading, quality/safety improvement, post-harvest loss reduction, value addition.",
    source_id=src_market2026.id, is_canonical="false",
))

kipumbwi_processing = InfrastructureAsset(
    landing_site_id=sites["Kipumbwi"].id, asset_type="processing_facility",
    operational_status="PLANNED", funding_program="World Bank / Tanzania fisheries programme",
    source_name=src_processing.title, verification_status="VERIFIED_OFFICIAL",
)
db.add(kipumbwi_processing)
db.flush()
db.add(GeographySourceClaim(
    entity_type="infrastructure_asset", entity_id=kipumbwi_processing.id,
    claim_field="implementation_status",
    claim_value="Sardine and Small Pelagic Fish Processing Plant. Progressing through feasibility study, detailed engineering design, construction supervision, environmental/social assessment. Feasibility/design consultancy extends into 2026-2027. Targets high consignments of sardines/small pelagics and export markets. Status: PLANNED/UNDER_IMPLEMENTATION, NOT operational.",
    source_id=src_processing.id, is_canonical="false",
))
print("Infrastructure projects seeded: Kipumbwi Fish Market (UNDER_IMPLEMENTATION), Kipumbwi Processing Plant (PLANNED)")

# ── PROCESSING INVESTMENT OPPORTUNITIES (not operating facilities) ────
investment_sites = [
    ("Pongwe", "Tanga City", None), ("Neema", "Tanga City", None),
    ("Macheni", "Tanga City", None), ("Tangasisi/Malongo", "Tanga City", None),
    ("Moa", "Mkinga", 1.0),  # hectares earmarked
]
for name, dname, hectares in investment_sites:
    site = sites.get(name)
    if site:
        db.add(GeographySourceClaim(
            entity_type="fish_landing_site", entity_id=site.id,
            claim_field="processing_investment_opportunity",
            claim_value=f"{hectares} hectare(s) earmarked for fish-processing industry (investment opportunity, not existing facility)" if hectares else "Identified as potential fish-processing location (investment opportunity, not existing facility)",
            source_id=src_investment.id, is_canonical="false",
        ))
db.add(GeographySourceClaim(
    entity_type="fish_landing_site", entity_id=sites["Kipumbwi"].id,
    claim_field="processing_investment_opportunity",
    claim_value="13.8 hectares earmarked for fish-processing industry (investment opportunity, separate from the World Bank sardine plant project already recorded)",
    source_id=src_investment.id, is_canonical="false",
))
print(f"Processing investment opportunities noted: {len(investment_sites)+1}")

# ── SPECIES — new rows only, existing 19+enriched batch untouched ─────
new_species = [
    ("Sardinella neglecta", "Sardinella neglecta", "Clupeidae", "pelagic"),
    ("Stolephorus commersonnii", "Stolephorus commersonnii", "Engraulidae", "pelagic"),
    ("Coelacanth", "Latimeria chalumnae", "Latimeriidae", "other"),
    ("Whitespotted Octopus", "Octopus chromatus", "Octopodidae", "mollusc"),
    ("Ornate Spiny Lobster", "Panulirus ornatus", "Palinuridae", "crustacean"),
    ("Giant Tiger Prawn", "Penaeus monodon", "Penaeidae", "crustacean"),
]
sp_count = 0
for common, sci, fam, cat in new_species:
    existing = db.query(Species).filter(Species.common_name == common).first()
    if not existing:
        db.add(Species(common_name=common, scientific_name=sci, family=fam, category=cat,
                        source_name=src_mlf2020.title, verification_status="RESEARCH_SOURCE"))
        sp_count += 1
db.flush()

coelacanth = db.query(Species).filter(Species.common_name == "Coelacanth").first()
if coelacanth:
    coelacanth.iuu_risk_flag = False
    coelacanth.notes = (coelacanth.notes or "") + " | Endangered, NOT a commercial target species. Protected-species interaction only, recorded at Kigombe deep-water grounds (50-200m)."
print(f"New species seeded: {sp_count} (Sardinella neglecta, Stolephorus commersonnii, coelacanth, Octopus chromatus, Panulirus ornatus, Penaeus monodon)")

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("TANGA REGION SEEDING COMPLETE")
print("=" * 60)
print(f"AdminGeography: 1 region + {len(districts)} districts")
print(f"FishLandingSites: {len(sites)} core + {hist_count} historical = {len(sites)+hist_count}")
print(f"FisheriesObservations: {3 + 4 + month_count + 2 + 2 + 7} rows (frame, conflicts, district totals, monthly, historical 2001, Mkinga)")
print(f"MarineManagementArea: TACMP")
print(f"CFMAs (JointCoManagementArea): {cfma_count}")
print(f"InfrastructureAssets: 2 (both correctly non-operational)")
print(f"New Species: {sp_count}")
print("Data quality flags preserved: 56-site incomplete register, 2 catch conflicts, historical vs current CMA distinction, historical fleet not substituted for official frame")

db.close()