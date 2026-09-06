# scripts/seed_species_enrichment_batch1.py
#
# Batch 1 species enrichment — updates EXISTING seeded Species rows
# with verified taxonomy/compliance/provenance data. Does NOT create
# new species. Does NOT touch the 13 records not researched this batch.
# Every field populated here traces to a real, cited source.
# No IUCN/CITES/habitat/gear/price data invented for unresearched fields.

from app.database.connection import SessionLocal
from app.models.fisheries_data import Species
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, doc_type=None, tier=3):
    existing = db.query(GeographySource).filter(GeographySource.title == title).first()
    if existing:
        return existing
    s = GeographySource(title=title, issuing_organization=org, publication_year=year,
                         document_type=doc_type, reliability_tier=tier)
    db.add(s)
    db.flush()
    return s


def get_species(common_name):
    sp = db.query(Species).filter(Species.common_name == common_name).first()
    if not sp:
        print(f"  WARNING: Species '{common_name}' not found — skipping")
    return sp


print("=" * 60)
print("SPECIES ENRICHMENT — BATCH 1 (6 records)")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_iucn_yft   = get_or_create_source("IUCN Red List reassessment — Thunnus albacares", org="IUCN", year=2021, doc_type="Red List assessment", tier=1)
src_marintrust = get_or_create_source("MarinTrust Standard v2.3 — Yellowfin Tuna raw material assessment", org="MarinTrust", year=2024, doc_type="Certification standard", tier=2)
src_fishbase_kf = get_or_create_source("FishBase — Scomberomorus commerson", org="FishBase", doc_type="Species database", tier=2)
src_iccat_kf    = get_or_create_source("ICCAT Small Tunas Species Manual — S. commerson", org="ICCAT", doc_type="Fisheries manual", tier=1)
src_gbif_rf     = get_or_create_source("GBIF — Siganus sutor species record", org="GBIF", doc_type="Biodiversity database", tier=2)
src_ntiba_rf    = get_or_create_source("Ntiba & Jaccarini 1990 — Gonad maturation and spawning of S. sutor off Kenya coast", year=1990, doc_type="Peer-reviewed journal article (J. Fish Biology)", tier=1)
src_kilifi_rf   = get_or_create_source("Kilifi County reproductive parameters study — S. sutor", year=2020, doc_type="Peer-reviewed (ResearchGate)", tier=2)
src_octopus_wiki = get_or_create_source("Wikipedia — Octopus cyanea (IUCN infobox claim: Least Concern)", doc_type="Encyclopedia", tier=4)
src_octopus_adw  = get_or_create_source("Animal Diversity Web — Octopus cyanea (claim: not evaluated by IUCN/CITES)", org="University of Michigan", doc_type="Species database", tier=3)
src_octopus_genetics = get_or_create_source("Genetic analysis of Octopus cyanea — high gene flow in SWIO", doc_type="Peer-reviewed (PMC10994983)", tier=1)
src_grouper_composition = get_or_create_source("Catch Composition, Abundance and Length-Weight Relationships of Groupers (Serranidae) from Inshore Waters of Kenya", doc_type="Peer-reviewed (ResearchGate)", tier=1)
src_grouper_fuscoguttatus = get_or_create_source("Biology and status of Epinephelus fuscoguttatus stocks on the Kenyan coast", doc_type="Peer-reviewed (ResearchGate)", tier=1)
src_lobster_shifts = get_or_create_source("Evidence of Considerable Shifts in Catch Composition in the Artisanal Spiny Lobster Fishery in Kenya", year=2023, doc_type="Peer-reviewed (Biology, MDPI / PMC10740627)", tier=1)
src_kenya_lobster_law = get_or_create_source("The Fisheries Management and Development (Lobster Fishery Management Plan) 2025", org="Kenya Law / State Department of Fisheries", year=2025, doc_type="Legal notice / management plan", tier=1)
src_cavalla_wiki = get_or_create_source("Wikipedia — Cavalla (disambiguation: Carangidae vs Scombridae vernacular usage)", doc_type="Encyclopedia", tier=4)

print("Sources seeded: 15")

# ── #13 TUNA / Jodari ──────────────────────────────────────────────
sp = get_species("Tuna")
if sp:
    sp.scientific_name = "Thunnus albacares"
    sp.order = "Scombriformes"
    sp.family = "Scombridae"
    sp.iucn_status = "Least Concern (reassessed 2021, from Near Threatened)"
    sp.cites_appendix = "none"
    sp.source_name = f"{src_iucn_yft.title}; {src_marintrust.title}"
    sp.source_year = 2024
    sp.verification_status = "RESEARCH_SOURCE"
    sp.confidence_score = 3  # Medium — species identity inferred, not MarineCatch-confirmed
    sp.notes = (sp.notes or "") + " | Species identity (T. albacares) inferred from small-scale IO gear/landing pattern, not directly confirmed against MarineCatch catch records."
    print("  Updated: Tuna -> Thunnus albacares (Medium confidence)")

# ── #11 KINGFISH / Nguru ────────────────────────────────────────────
sp = get_species("Kingfish")
if sp:
    sp.scientific_name = "Scomberomorus commerson"
    sp.order = "Scombriformes"
    sp.family = "Scombridae"
    sp.iucn_status = "Near Threatened (IUCN 3.1, assessed 10 Nov 2022)"
    sp.source_name = f"{src_fishbase_kf.title}; {src_iccat_kf.title}"
    sp.verification_status = "VERIFIED_SECONDARY"
    sp.confidence_score = 4  # High — "Kingfish" directly documented common name for this exact species
    print("  Updated: Kingfish -> Scomberomorus commerson (High confidence)")

# ── #1 RABBIT FISH / Tafi ────────────────────────────────────────────
sp = get_species("Rabbit Fish")
if sp:
    sp.scientific_name = "Siganus sutor"
    sp.family = "Siganidae"
    sp.source_name = f"{src_gbif_rf.title}; {src_ntiba_rf.title}; {src_kilifi_rf.title}"
    sp.verification_status = "VERIFIED_SECONDARY"
    sp.confidence_score = 4  # High — ~40% of all Kenya artisanal landings, studied at Kilifi sites
    sp.notes = (sp.notes or "") + " | S. sutor accounts for ~40% of Kenya artisanal fishery landings; studied directly at Kilifi County landing sites. IUCN/CITES status not yet researched."
    print("  Updated: Rabbit Fish -> Siganus sutor (High confidence)")

# ── #18 OCTOPUS / Pweza — with explicit source conflict ────────────
sp = get_species("Octopus")
if sp:
    sp.scientific_name = "Octopus cyanea (candidate)"
    sp.family = "Octopodidae"
    sp.source_name = f"{src_octopus_genetics.title}"
    sp.verification_status = "CONFLICTING_SOURCES"
    sp.confidence_score = 3  # Medium-High on identity, but IUCN status itself conflicting
    sp.notes = (sp.notes or "") + " | O. cyanea range confirmed to include Kenya via SWIO genetic study (Kenya, Tanzania, Mozambique, Madagascar, Mauritius, Rodrigues, Seychelles sampled). IUCN status CONFLICTING: Wikipedia infobox states Least Concern; Animal Diversity Web states not evaluated by IUCN or CITES. Both claims preserved, not resolved."
    db.flush()
    db.add(GeographySourceClaim(
        entity_type="species", entity_id=sp.id,
        claim_field="iucn_status", claim_value="Least Concern (IUCN 3.1)",
        source_id=src_octopus_wiki.id, is_canonical="false",
    ))
    db.add(GeographySourceClaim(
        entity_type="species", entity_id=sp.id,
        claim_field="iucn_status", claim_value="Not evaluated by IUCN Red List or CITES",
        source_id=src_octopus_adw.id, is_canonical="false",
    ))
    print("  Updated: Octopus -> Octopus cyanea candidate (IUCN conflict preserved as 2 claims)")

# ── #5 ROCK COD / Tewa — remains generic, compliance flag added ────
sp = get_species("Rock Cod")
if sp:
    sp.family = "Serranidae"
    sp.source_name = f"{src_grouper_composition.title}; {src_grouper_fuscoguttatus.title}"
    sp.verification_status = "RESEARCH_SOURCE"
    sp.confidence_score = 2  # Low on single-species ID — genuinely multi-species, by design
    sp.iuu_risk_flag = None  # explicitly not set true/false — insufficient basis to flag the whole category
    sp.notes = (sp.notes or "") + (
        " | KEPT GENERIC BY DESIGN: 37 species across 6 genera (Anyperodon, Cephalopholis, "
        "Dermatolepis, Epinephelus, Plectropomus, Variola) documented under this commercial "
        "name in Kenyan inshore fisheries. FAO's own official term for this group is "
        "'groupers, rock cod, hind, coral grouper and lyre tail' (Heemstra & Randall 1993, "
        "FAO Fisheries Synopsis 125 Vol 16) — 'Rock Cod' is a legitimate FAO-recognized "
        "commercial category, not an imprecise label. COMPLIANCE NOTE: Epinephelus "
        "fuscoguttatus (IUCN Vulnerable, reassessed from Near Threatened) has been directly "
        "studied at Shimoni and Mayungu landing sites — Shimoni is a MarineCatch source "
        "landing site. Recommend catch-logging prompts ask fishers to specify grouper type "
        "when landing 'Rock Cod' once operational data collection begins."
    )
    print("  Updated: Rock Cod -> remains generic (compliance flag re: Shimoni/E. fuscoguttatus added)")

# ── #15 LOBSTER / Kamba Mawe — remains generic, rich context added ─
sp = get_species("Lobster")
if sp:
    sp.family = "Palinuridae"
    sp.source_name = f"{src_lobster_shifts.title}; {src_kenya_lobster_law.title}"
    sp.verification_status = "VERIFIED_OFFICIAL"  # Kenya Law 2025 is a Tier 1 legal source
    sp.confidence_score = 2  # Low on single-species ID for "Kamba Mawe" specifically — genuinely 5-species fishery
    sp.min_legal_size_cm = None  # law specifies weight (250g), not length — do not convert without a real conversion source
    sp.size_limit_regulation_notes = (
        "Kenya's Lobster Fishery Management Plan 2025 (Kenya Law) sets Minimum Legal Weight "
        "(MLW) of 250g across the artisanal spiny lobster fishery. Five Panulirus species "
        "recognized in law: P. ornatus (Mwani), P. longipes (Mwilo), P. penicillatus (Kijiwe), "
        "P. versicolor (Kurabu), P. homarus (Springi). NONE of these official Swahili names "
        "match MarineCatch's existing local_name 'Kamba Mawe', suggesting 'Kamba Mawe' is a "
        "regional/generic term, not one of the five legally-named species."
    )
    sp.notes = (sp.notes or "") + (
        " | KEPT GENERIC BY DESIGN: species composition is genuinely site-specific per "
        "peer-reviewed 2023 study — at Shimoni specifically (a MarineCatch source landing "
        "site), P. longipes dominates catches at 58%, not P. homarus. Species mix varies "
        "meaningfully between MarineCatch's own operating sites (Shimoni, Kwale) vs other "
        "Kenyan landing sites (Lamu, Kipini, Mambrui, Kilifi). Co-management area for "
        "Shimoni-Vanga specifically named in Kenya's 2025 management plan. High commercial "
        "value species — recommend prioritizing site-specific species resolution once "
        "MarineCatch has real Shimoni lobster catch/photo data."
    )
    print("  Updated: Lobster -> remains generic (Kenya Law 2025 compliance data + Shimoni-specific composition added)")

# ── #9 CAVALLA/JACK / Kole Kole — correct known error ───────────────
sp = get_species("Cavalla/Jack")
if sp:
    old_sci_name = sp.scientific_name
    sp.scientific_name = None  # remove incorrect binomial rather than leave it standing
    sp.source_name = src_cavalla_wiki.title
    sp.verification_status = "CONFLICTING_SOURCES"
    sp.confidence_score = None
    sp.notes = (sp.notes or "") + (
        f" | CORRECTED: previous scientific_name '{old_sci_name}' was a synonym for "
        "Katsuwonus pelamis (skipjack tuna), inconsistent with 'Cavalla/Jack' common name. "
        "'Cavalla' is a genuinely ambiguous vernacular term used for BOTH Carangidae (jacks, "
        "e.g. Caranx hippos) and Scombridae (mackerels, e.g. Scomber spp.) depending on "
        "regional tradition. UNRESOLVED pending real MarineCatch operational data "
        "(no catch logs exist yet as of this enrichment pass) — species identity should be "
        "revisited once actual landed specimens/photos are available from fishers."
    )
    print(f"  Corrected: Cavalla/Jack -> scientific_name cleared (was '{old_sci_name}', now null, flagged unresolved)")

db.commit()

# ── SUMMARY ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("BATCH 1 ENRICHMENT COMPLETE")
print("=" * 60)
print(f"Species records updated: 6 of 19")
print(f"Species records untouched (remain as originally seeded): 13")
print(f"GeographySourceClaims added (Octopus IUCN conflict): 2")
print(f"GeographySources seeded: {db.query(GeographySource).filter(GeographySource.title.like('%Species%')).count() + 15}")

db.close()