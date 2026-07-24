# app/services/compliance_assistant_service.py
#
# WHY THIS FILE EXISTS:
# Guides fishers through KRA PIN registration and compliance
# questions via natural WhatsApp conversation — grounded in
# their actual compliance profile data.

import anthropic
from app.config import settings
from sqlalchemy.orm import Session

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a compliance assistant for MarineCatch Africa, \
helping fishers understand KRA tax compliance in simple terms.

RULES:
- Only use the DATA CONTEXT provided about this fisher's profile.
- Keep responses under 60 words — this is WhatsApp.
- Be encouraging, not bureaucratic. Explain benefits, not just rules.
- If they want to submit their KRA PIN, tell them: type "KRA " followed \
by their PIN, e.g. "KRA A123456789B"
- If they don't have a KRA PIN yet, explain simply: visit any KRA office \
or Huduma Centre with their National ID, it's free and takes about 30 minutes.
- Never discuss tax rates, penalties, or give legal/tax advice — only \
explain the MarineCatch registration process.

DATA CONTEXT:
{data_context}
"""


async def answer_compliance_question(
    db:           Session,
    fisher_id:    int,
    user_message: str,
) -> str:
    """
    Answer a fisher's natural language question about KRA/compliance,
    grounded in their actual compliance profile.
    """
    from app.models.compliance_profile import ComplianceProfile

    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == fisher_id
    ).first()

    if profile:
        data_context = (
            f"Member ID: {profile.member_id or 'not yet assigned'}\n"
            f"Compliance level: {profile.compliance_level} (1=Registered, "
            f"2=BMU Verified, 3=Tax Compliant, 4=Export Ready)\n"
            f"KRA verified: {'Yes' if profile.kra_verified else 'No'}\n"
            f"Total sales through MarineCatch: KES {profile.total_value_kes:,.0f}\n"
        )
    else:
        data_context = "No compliance profile found yet for this fisher."

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=SYSTEM_PROMPT.format(data_context=data_context),
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"Compliance assistant error: {e}")
        return (
            "To add your KRA PIN, type:\n*KRA A123456789B*\n\n"
            "Don't have one? Visit any KRA office or Huduma Centre "
            "with your National ID — it's free.\n\n"
            "MarineCatch Africa 🐟"
        )