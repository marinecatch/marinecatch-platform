# app/services/price_intelligence_service.py
#
# WHY THIS FILE EXISTS:
# Suggests optimal selling price to fishers based on BMU
# historical data and current marketplace demand — grounded
# in real data, never invented figures.

import anthropic
from app.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import func

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a price intelligence assistant for MarineCatch \
Africa, helping fishers understand fair market pricing for their catch.

RULES:
- Only use the DATA CONTEXT provided. Never invent prices.
- Keep response under 50 words — this goes to WhatsApp.
- Be encouraging and clear, use 1 relevant emoji max.
- Always mention the price is a suggestion, final price is set by \
MarineCatch after inspection (covers commission, cold chain, logistics).

DATA CONTEXT:
{data_context}
"""


async def suggest_price(
    db:      Session,
    species: str,
    weight_kg: float,
) -> str:
    """
    Suggest a fair asking price for a fisher's catch based on
    BMU historical data and current live inventory prices.
    """
    from app.models.fisheries_data import HistoricalLanding
    from app.models.inventory_lot import InventoryLot, LotStatus

    # Historical BMU average
    historical = db.query(
        func.avg(HistoricalLanding.price_per_kg).label('avg_price'),
        func.min(HistoricalLanding.price_per_kg).label('min_price'),
        func.max(HistoricalLanding.price_per_kg).label('max_price'),
    ).filter(
        HistoricalLanding.species_common.ilike(f"%{species}%"),
        HistoricalLanding.price_per_kg > 0,
    ).first()

    # Current live marketplace prices
    live_lots = db.query(InventoryLot).filter(
        InventoryLot.species == species.lower(),
        InventoryLot.lot_status == LotStatus.AVAILABLE,
        InventoryLot.selling_price_per_kg > 0,
    ).all()

    live_prices = [l.selling_price_per_kg for l in live_lots]
    live_avg = sum(live_prices) / len(live_prices) if live_prices else None

    data_lines = [f"Species: {species}", f"Weight: {weight_kg}kg"]
    if historical and historical.avg_price:
        data_lines.append(
            f"BMU historical average: KES {historical.avg_price:.0f}/kg "
            f"(range KES {historical.min_price:.0f}-{historical.max_price:.0f})"
        )
    if live_avg:
        data_lines.append(f"Current marketplace average: KES {live_avg:.0f}/kg")

    if len(data_lines) == 2:
        data_lines.append("No historical or live pricing data available for this species.")

    data_context = "\n".join(data_lines)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=SYSTEM_PROMPT.format(data_context=data_context),
            messages=[{
                "role": "user",
                "content": f"What price should I ask for {weight_kg}kg of {species}?"
            }],
        )
        return response.content[0].text
    except Exception as e:
        print(f"Price intelligence error: {e}")
        if historical and historical.avg_price:
            return (
                f"💰 Based on past data, {species.title()} averages "
                f"KES {historical.avg_price:.0f}/kg. Suggest asking around this price.\n"
                f"Final price set by MarineCatch after inspection."
            )
        return (
            f"No pricing data available for {species.title()} yet. "
            f"Please provide your asking price and MarineCatch will "
            f"advise a fair market price after inspection."
        )