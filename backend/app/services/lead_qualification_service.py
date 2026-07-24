# app/services/lead_qualification_service.py
#
# WHY THIS FILE EXISTS:
# Auto-scores and prioritizes leads from the landing page
# based on role, location, and message content — so Muna
# and the sales team know who to contact first.

import anthropic
from app.config import settings
from sqlalchemy.orm import Session

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a lead scoring assistant for MarineCatch Africa, \
a seafood supply chain platform in Kenya. Score incoming leads to help \
the sales team prioritize follow-up.

Score from 1-10 based on:
- Institutional/high-volume buyers (hotels, processors, exporters) = higher score
- Clear species/volume interest mentioned = higher score
- Vague or single-item enquiries = lower score
- Investors/media = medium score (relationship value, not immediate revenue)
- Location near Diani/Kwale/Mombasa (existing operations) = higher score

Respond with ONLY a JSON object, no other text:
{"score": <1-10>, "priority": "<high|medium|low>", "reason": "<one short sentence>"}
"""


def score_lead(
    name:     str,
    role:     str,
    location: str,
    message:  str,
) -> dict:
    """
    Score a new lead for sales prioritization.
    Falls back to a simple rule-based score if AI is unavailable.
    """
    lead_summary = (
        f"Name: {name}\nRole: {role}\nLocation: {location or 'not provided'}\n"
        f"Message: {message or 'none provided'}"
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": lead_summary}],
        )
        import json
        result = json.loads(response.content[0].text.strip())
        return result
    except Exception as e:
        print(f"Lead scoring AI failed, using fallback: {e}")
        # Rule-based fallback
        high_value_roles = ["buyer_hotel", "processor", "investor"]
        score = 7 if role in high_value_roles else 4
        priority = "high" if score >= 7 else "medium" if score >= 4 else "low"
        return {
            "score": score,
            "priority": priority,
            "reason": "Rule-based scoring (AI unavailable)",
        }