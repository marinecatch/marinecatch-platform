# app/services/whatsapp_ai_service.py
#
# WHY THIS FILE EXISTS:
# Natural language understanding layer for WhatsApp buyer queries.
# Works ALONGSIDE the existing menu/command system — not a replacement.
#
# When a buyer's message doesn't match any known command
# (fish, order, price, menu, etc.), we fall back to this AI
# assistant to understand intent and either:
# 1. Answer directly from live inventory/price data
# 2. Guide them to the right command
#
# Uses Claude Haiku for cost efficiency at WhatsApp scale.
# Every AI response includes real data — never invents prices,
# species, or availability. This is critical for trust.

import anthropic
from app.config import settings
from sqlalchemy.orm import Session

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are the WhatsApp assistant for MarineCatch Africa, \
a seafood supply chain platform in Kenya. You help buyers (hotels, \
restaurants, processors) with questions about seafood availability, \
pricing, and ordering.

RULES:
- Only state facts from the DATA CONTEXT provided below. Never invent \
prices, species, or availability.
- If asked something not covered by the data, tell them to type MENU \
for options or contact support.
- Keep responses under 60 words — this is WhatsApp, not email.
- Always be warm but efficient. Use 1-2 relevant emoji, not more.
- If they want to place an order, tell them the exact command: \
"ORDER species quantity" e.g. "ORDER tuna 20"
- Never discuss competitors, pricing strategy, or internal operations.
- If asked about something unrelated to seafood/MarineCatch, politely \
redirect to MENU.

DATA CONTEXT:
{data_context}
"""


async def get_ai_response(
    db:           Session,
    user_message: str,
) -> str:
    """
    Generate a natural language response to a buyer's WhatsApp message
    that didn't match a known command.

    Builds live data context from current inventory before calling
    the model, so responses are always grounded in real data.
    """
    from app.services.inventory_service import get_available_lots

    lots = get_available_lots(db, limit=15)

    if lots:
        data_lines = []
        seen_species = set()
        for lot in lots:
            if lot.species not in seen_species:
                data_lines.append(
                    f"- {lot.species.title()}: {lot.available_kg}kg available "
                    f"at KES {lot.selling_price_per_kg}/kg, "
                    f"location: {lot.landing_site.title()}"
                )
                seen_species.add(lot.species)
        data_context = "\n".join(data_lines)
    else:
        data_context = "No seafood currently available in inventory."

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=SYSTEM_PROMPT.format(data_context=data_context),
            messages=[
                {"role": "user", "content": user_message}
            ],
        )
        return response.content[0].text
    except Exception as e:
        print(f"WhatsApp AI error: {e}")
        return (
            "Sorry, I didn't quite catch that. 🤔\n\n"
            "Type *MENU* to see options, or *FISH* to browse "
            "available seafood."
        )