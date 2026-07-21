# app/models/newsletter_subscriber.py
#
# WHY THIS FILE EXISTS:
# MarineCatch Blue Economy Intelligence — a stakeholder
# relationship engine, not just an email list.
#
# Every subscriber is segmented by stakeholder type so future
# newsletters can be targeted: investors get metrics, government
# gets policy/compliance updates, buyers get price intelligence,
# fishers get market opportunities.

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime, timezone
from app.database.connection import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id                = Column(Integer, primary_key=True, index=True)
    email             = Column(String(200), unique=True, nullable=False, index=True)
    name              = Column(String(100), nullable=True)
    organization      = Column(String(150), nullable=True)

    stakeholder_type  = Column(String(30), default="other")
    # investor, government, buyer, supplier, processor,
    # research, partner, media, other

    country           = Column(String(50), nullable=True)
    source            = Column(String(50), nullable=True)
    # landing_page, footer, conference, referral

    consent           = Column(Boolean, default=True)
    status            = Column(String(20), default="pending")
    # pending, confirmed, unsubscribed

    utm_source        = Column(String(100), nullable=True)
    utm_campaign      = Column(String(100), nullable=True)

    last_opened_at    = Column(DateTime(timezone=True), nullable=True)
    notes             = Column(Text, nullable=True)

    created_at        = Column(DateTime(timezone=True),
                               default=lambda: datetime.now(timezone.utc))
    updated_at        = Column(DateTime(timezone=True),
                               onupdate=lambda: datetime.now(timezone.utc))