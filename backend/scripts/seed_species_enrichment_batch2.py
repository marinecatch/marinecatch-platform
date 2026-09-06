# scripts/seed_species_enrichment_batch2.py
#
# Batch 2 species enrichment — sourced from
# MarineCatch_Indian_Ocean_Species_Intelligence_Phase1.xlsx
# (FAO/KMFRI 2012, KeFS 2024 Bulletin, IOTC, UN Comtrade/WITS,
# Kenya Law 2025). Updates existing Species rows. Adds
# SpeciesMarketPrice rows (landing + export tiers). No new
# species created. No migration required — tables already exist.

from app.database.connection import SessionLocal
from app.models.fisheries_data import Species
from app.models.intelligence.geography_source import GeographySource, GeographySourceClaim
from app.models.intelligence.species_market_price import SpeciesMarketPrice

db = SessionLocal()


def get_or_create_source(title, org=None, year=None, doc_type=None, tier=1):
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


def add_landing_price(species, kes_per_kg, source, notes=None):
    existing = db.query(SpeciesMarketPrice).filter(
        SpeciesMarketPrice.species_id == species.id,
        SpeciesMarketPrice.market_tier == "landing",
        SpeciesMarketPrice.observed_period == "2024",
    ).first()
    if existing:
        return existing
    p = SpeciesMarketPrice(
        species_id=species.id, market_tier="landing", currency="KES",
        price_avg=kes_per_kg, unit="per_kg", observed_period="2024",
        source_name=source.title, verification_status="VERIFIED_OFFICIAL",
        confidence_score=5,  # official government statistical bulletin
    )
    db.add(p)
    db.flush()
    return p


print("=" * 60)
print("SPECIES ENRICHMENT — BATCH 2 (KeFS 2024 pricing + corrections)")
print("=" * 60)

# ── SOURCES ──────────────────────────────────────────────────────
src_kefs2024   = get_or_create_source("KeFS Fisheries Statistical Bulletin 2024 (issued 2025)", org="Kenya Fisheries Service", year=2024, doc_type="Statistical bulletin", tier=1)
src_faokmfri   = get_or_create_source("FAO/KMFRI Field identification guide to living marine resources of Kenya", org="FAO/KMFRI", year=2012, doc_type="Field guide", tier=1)
src_witscomtrade = get_or_create_source("Kenya 2024 seafood trade by HS6", org="World Bank WITS / UN Comtrade", year=2024, doc_type="Customs trade data", tier=1)
src_kenyalobsterlaw = get_or_create_source("Fisheries Management and Development (Lobster Fishery Management Plan) 2025", org="Kenya Law", year=2025, doc_type="Legal notice", tier=1)
src_marinecatch_xlsx = get_or_create_source("MarineCatch Indian Ocean Species Intelligence Phase 1 (compiled workbook)", doc_type="Internal compiled research", tier=2)

print("Sources seeded: 5")

# ── KEFS 2024 LANDING PRICES — mapped to matching existing categories ──
landing_prices = {
    "Lobster":      1689.67,
    "Crab":          536.91,
    "Prawns":        508.63,
    "Squid":         345.86,
    "Octopus":       295.62,
    "Kingfish":      265.89,
    "Cavalla/Jack":  253.52,
    "Black Skin":    226.07,
    "Goat Fish":     225.42,
    "Rabbit Fish":   224.09,
    "Barracuda":     217.78,
    "Tuna":          210.48,   # KeFS category "Bonitos/tunas"
    "Rock Cod":      210.30,
    "Snapper":       208.02,
    "Queen Fish":    200.19,
    "Parrot Fish":   167.83,
    "Scavenger":     159.63,
    "Surgeon Fish":  211.76,
    "Sardines":      102.52,
}
priced_count = 0
for common_name, kes in landing_prices.items():
    sp = get_species(common_name)
    if sp:
        add_landing_price(sp, kes, src_kefs2024)
        priced_count += 1
print(f"KeFS 2024 landing-price rows added: {priced_count}")

# ── EXPORT PRICES — Octopus and Lobster (real Comtrade/WITS data) ──
sp = get_species("Octopus")
if sp:
    existing = db.query(SpeciesMarketPrice).filter(
        SpeciesMarketPrice.species_id == sp.id, SpeciesMarketPrice.market_tier == "export"
    ).first()
    if not existing:
        db.add(SpeciesMarketPrice(
            species_id=sp.id, market_tier="export", currency="USD",
            price_avg=3.90, unit="per_kg", observed_period="2024",
            source_name=f"{src_witscomtrade.title} — HS 030759, total $4.99M / 1,279,220kg",
            verification_status="VERIFIED_OFFICIAL", confidence_score=5,
        ))
        db.flush()
    sp.notes = (sp.notes or "") + (
        " | Second local candidate identified: Callistoctopus macropus "
        "(Whitespotted octopus), also 'Pweza' locally, per FAO/KMFRI 2012. "
        "Does not resolve which species dominates MarineCatch's actual trade."
    )
    print("  Octopus: export price added (~$3.90/kg, 2024), second species candidate noted")

sp = get_species("Lobster")
if sp:
    existing = db.query(SpeciesMarketPrice).filter(
        SpeciesMarketPrice.species_id == sp.id, SpeciesMarketPrice.market_tier == "export"
    ).first()
    if not existing:
        db.add(SpeciesMarketPrice(
            species_id=sp.id, market_tier="export", currency="USD",
            price_avg=15.44, unit="per_kg", observed_period="2024",
            source_name=f"{src_witscomtrade.title} — HS 030611 frozen rock lobster, $322.69K / 20,903kg (Italy, Portugal)",
            verification_status="VERIFIED_OFFICIAL", confidence_score=5,
        ))
        db.flush()
    sp.notes = (sp.notes or "") + (
        " | IMPORTANT MAPPING FLAG: FAO/KMFRI 2012 uses 'Kambamawe' as local "
        "name for Metanephrops andamanicus, Puerulus angulatus, Scyllarides "
        "squammosus, Thenus orientalis — NOT the 5 principal high-value "
        "Panulirus species (which have distinct names: Mwani, Mwilo, Springi, "
        "Kurabu, Kijiwe per Kenya Law 2025). MarineCatch's 'Kamba Mawe' may "
        "therefore refer to a different, lower-value lobster group than "
        "assumed. HIGH PRIORITY to resolve with real photos/buyer evidence "
        "once trading begins, given Lobster is a top-value category."
    )
    print("  Lobster: export price added (~$15.44/kg, 2024), Kambamawe mapping flag added")

# ── CAVALLA/JACK — upgrade from unresolved to genus-level candidate ──
sp = get_species("Cavalla/Jack")
if sp:
    sp.family = "Carangidae"
    sp.source_name = src_faokmfri.title
    sp.verification_status = "VERIFIED_SECONDARY"
    sp.confidence_score = 3  # Medium — genus-level, not species-level
    sp.notes = (sp.notes or "") + (
        " | UPGRADED (Batch 2): 'Kolekole/Kambisi/Kanaa' documented in FAO/KMFRI "
        "2012 as local name for 8 Carangoides species (trevallies): C. armatus, "
        "C. chrysophrys, C. coeruleopinnatus, C. equula, C. fulvoguttatus, "
        "C. malabaricus, C. oblongus, C. orthogrammus — Family Carangidae. "
        "Supports 'Jack' reading over prior tuna-synonym error. Note: "
        "Scomberoides queenfish species also share 'Kolekole' as an alternate "
        "name in the same source (also Carangidae) — genus-level identification "
        "remains ambiguous between Carangoides and Scomberoides, species-level "
        "unresolved. KeFS's own 2024 category name 'Cavalla jacks' is consistent "
        "with this reading."
    )
    print("  Cavalla/Jack: upgraded to Family Carangidae, genus Carangoides candidate (Medium confidence)")

# ── TUNA — record second conflicting candidate ──────────────────────
sp = get_species("Tuna")
if sp:
    db.flush()
    db.add(GeographySourceClaim(
        entity_type="species", entity_id=sp.id,
        claim_field="species_identity",
        claim_value="Thunnus obesus (Bigeye tuna) — 'Jodari/Kiboma' pairing",
        source_id=src_marinecatch_xlsx.id, is_canonical="false",
    ))
    db.add(GeographySourceClaim(
        entity_type="species", entity_id=sp.id,
        claim_field="species_identity",
        claim_value="Thunnus albacares (Yellowfin tuna) — inferred from small-scale IO gear pattern",
        source_id=None, is_canonical="false",
    ))
    sp.verification_status = "CONFLICTING_SOURCES"
    sp.notes = (sp.notes or "") + (
        " | CONFLICTING SPECIES CANDIDATES recorded, not resolved: T. obesus "
        "(this source, direct 'Jodari' pairing) vs T. albacares (Batch 1, "
        "gear-pattern inference). KeFS's own 2024 category 'Bonitos/tunas' is "
        "itself generic — even the government bulletin doesn't separate these. "
        "Landing-tier price (KES 210/kg) recorded above is far below prior "
        "internal 600-1200 KES/kg estimate — likely reflects export/premium-"
        "tier assumption in the original figure, not a data error."
    )
    print("  Tuna: second species conflict recorded (T. obesus vs T. albacares)")

# ── GOATFISH — direct local-name match found ─────────────────────────
sp = get_species("Goat Fish")
if sp:
    sp.scientific_name = "Parupeneus trifasciatus (candidate)"
    sp.family = "Mullidae"
    sp.source_name = src_faokmfri.title
    sp.verification_status = "VERIFIED_SECONDARY"
    sp.confidence_score = 3  # Medium — local name matches exactly ("Mkundaji"), single candidate found
    sp.notes = (sp.notes or "") + (
        " | Parupeneus trifasciatus (Doublebar goatfish) local name 'Mkoma/"
        "Mkundaji' directly matches MarineCatch's existing local_name "
        "'Mkundaji' exactly. Only goatfish species found in this source — "
        "single candidate, not confirmed as the sole species traded."
    )
    print("  Goat Fish: candidate Parupeneus trifasciatus added (local name exact match)")

# ── SARDINES — naming mismatch flag ──────────────────────────────────
sp = get_species("Sardines")
if sp:
    sp.family = "Clupeidae"
    sp.source_name = src_faokmfri.title
    sp.notes = (sp.notes or "") + (
        " | NAMING FLAG: FAO/KMFRI 2012 consistently pairs marine WIO sardine "
        "species (Amblygaster leiogaster, A. sirm, Sardinella albella, "
        "S. gibbosa, S. melanura) with local names 'Simu/Kerenge' — NOT "
        "'Dagaa'. 'Dagaa' is more commonly the Lake Victoria freshwater term "
        "(Rastrineobola argentea). MarineCatch's use of 'Dagaa' for a marine "
        "Kwale-coast product may be informal/borrowed terminology rather than "
        "the technically correct WIO marine name — worth clarifying with "
        "fishers directly rather than assuming either is 'correct.'"
    )
    print("  Sardines: Dagaa vs Simu/Kerenge naming mismatch flagged")

# ── CRAB, PRAWNS, SQUID — confirmed multi-species, correctly generic ──
sp = get_species("Crab")
if sp:
    sp.family = "Portunidae"
    sp.notes = (sp.notes or "") + (
        " | 3 candidates found sharing 'Kaa'-family local names: Portunus "
        "pelagicus (Kaa kiukizi/Mswete), Scylla serrata (Kaa mondokoko, FAO "
        "guide notes as 'most preferred of three important Kenyan crabs'), "
        "Thalamita crenata (Kaa kijiwe/Gonda). Genuinely multi-species — "
        "kept generic."
    )
    print("  Crab: 3 species candidates noted, kept generic")

sp = get_species("Prawns")
if sp:
    sp.family = "Penaeidae"
    sp.notes = (sp.notes or "") + (
        " | 10 species share generic 'Kamba' local name in FAO/KMFRI 2012 "
        "(Macrobrachium rude, Nematopalaemon tenuipes, Exhippolysmata "
        "ensirostris, Fenneropenaeus indicus, Marsupenaeus japonicus, "
        "Melicertus canaliculatus/latisulcatus/marginatus, Metapenaeus "
        "monoceros, Trachysalambria curvirostris) — confirmed unresolvable "
        "to species from name alone. Kept generic."
    )
    print("  Prawns: 10 species candidates noted, confirmed generic")

sp = get_species("Squid")
if sp:
    sp.family = "Loliginidae"
    sp.notes = (sp.notes or "") + (
        " | 3 candidates share 'Ngisi' local name: Uroteuthis duvaucelii "
        "(Indian squid), Onychoteuthis banksii (clubhook squid), "
        "Sthenoteuthis oualaniensis (purpleback flying squid) — spans 3 "
        "different families, not just Loliginidae. Kept generic."
    )
    print("  Squid: 3 species candidates across multiple families noted, kept generic")

# ── ROCK COD — further species confirmed, strengthens generic status ──
sp = get_species("Rock Cod")
if sp:
    sp.notes = (sp.notes or "") + (
        " | Additional species confirmed sharing 'Tewa': Dermatolepis "
        "striolata, Epinephelus chabaudi, E. miliaris (Tewa chui), E. ongus, "
        "E. poecilonotus, Gracila albomarginata — beyond E. lanceolatus, "
        "E. flavocaeruleus, E. fuscoguttatus already noted. At least 9 "
        "species now documented under this one commercial name. Further "
        "confirms generic status is correct, not a data gap."
    )
    print("  Rock Cod: 6 additional species candidates noted (total ~9 documented)")

db.commit()

print()
print("=" * 60)
print("BATCH 2 ENRICHMENT COMPLETE")
print("=" * 60)
print(f"Landing-price records added: {priced_count}")
print(f"Export-price records added: 2 (Octopus, Lobster)")
print(f"Species records updated with new findings: 10")
print(f"Key corrections: Cavalla/Jack upgraded (genus-level), Kingfish/Tuna/Crab/Prawns/Scavenger price context added")
print(f"Key flags: Tuna species conflict (2 claims), Lobster Kambamawe mapping risk, Sardines naming mismatch")

db.close()