# app/models/lead_attribution.py
#
# WHY THIS FILE EXISTS:
# Every user and lead on MarineCatch Africa has an acquisition story.
# This model captures the complete context of how they found us.
#
# This powers:
# - Channel performance analysis
# - Partner attribution (OOC, SoteHub, KFS, KMFRI)
# - QR code campaign tracking
# - Embedded finance eligibility (operational history starts here)
# - Conversion funnel analysis
#
# Registration sources:
# website, whatsapp, ussd, admin, partner, api, mobile_app, qr_code

from sqlalchemy import (Column, Integer, String, Boolean,
                        DateTime, ForeignKey, Text)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class LeadAttribution(Base):
    __tablename__ = "lead_attributions"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"),
                                nullable=True, index=True)
    # Null until lead converts to registered user

    # ── SESSION ───────────────────────────────────────────────────
    session_id          = Column(String(100), nullable=True)

    # ── UTM PARAMETERS ────────────────────────────────────────────
    utm_source          = Column(String(100), nullable=True)
    # linkedin, instagram, tiktok, twitter, facebook,
    # google, whatsapp, direct, ussd, qr_code
    utm_medium          = Column(String(100), nullable=True)
    # social, email, referral, organic, paid, event
    utm_campaign        = Column(String(100), nullable=True)
    # ooc2026, launch_july, fisher_onboarding
    utm_term            = Column(String(100), nullable=True)
    utm_content         = Column(String(100), nullable=True)

    # ── PARTNER ATTRIBUTION ───────────────────────────────────────
    partner_code        = Column(String(50), nullable=True, index=True)
    # OOC2026, SOTEHUB, OCEANHUB, KATAPULT, KMFRI, KFS, KFIC, KFMA
    partner_campaign    = Column(String(100), nullable=True)
    partner_referrer    = Column(String(100), nullable=True)

    # ── PAGE / REFERRER ───────────────────────────────────────────
    referrer            = Column(String(500), nullable=True)
    # Full referring URL
    landing_page        = Column(String(200), nullable=True)
    # Page they landed on: /, /buyer, /fisher, /insights/...

    # ── REGISTRATION SOURCE ───────────────────────────────────────
    registration_source = Column(String(30), nullable=True)
    # website, whatsapp, ussd, admin, partner, api, mobile_app, qr_code

    # ── DEVICE / BROWSER ─────────────────────────────────────────
    device              = Column(String(30), nullable=True)
    # mobile, desktop, tablet
    browser             = Column(String(50), nullable=True)
    os                  = Column(String(50), nullable=True)

    # ── GEO ───────────────────────────────────────────────────────
    country             = Column(String(50), nullable=True)
    city                = Column(String(100), nullable=True)
    ip_hash             = Column(String(64), nullable=True)
    # Hashed for privacy compliance

    # ── LEAD DATA ─────────────────────────────────────────────────
    lead_name           = Column(String(100), nullable=True)
    lead_phone          = Column(String(20), nullable=True)
    lead_email          = Column(String(200), nullable=True)
    lead_role           = Column(String(50), nullable=True)
    # fisher, supplier, buyer_hotel, buyer_restaurant, investor, etc.
    lead_location       = Column(String(200), nullable=True)
    lead_message        = Column(Text, nullable=True)

    # ── CONVERSION TRACKING ───────────────────────────────────────
    converted_to_user   = Column(Boolean, default=False)
    converted_at        = Column(DateTime(timezone=True), nullable=True)
    converted_order_id  = Column(Integer, ForeignKey("orders.id"), nullable=True)
    # First order placed after registration

    # ── VISIT TRACKING ────────────────────────────────────────────
    first_visit         = Column(DateTime(timezone=True), nullable=True)
    last_visit          = Column(DateTime(timezone=True), nullable=True)

    # ── TIMESTAMPS ────────────────────────────────────────────────
    created_at          = Column(DateTime(timezone=True),
                                default=lambda: datetime.now(timezone.utc))

    # ── RELATIONSHIPS ─────────────────────────────────────────────
    user                = relationship("User", foreign_keys=[user_id])