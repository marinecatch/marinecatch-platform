# app/models/whatsapp_message.py
#
# WHY THIS FILE EXISTS:
# The WhatsApp Cloud API has no built-in inbox. Every message
# in and out passes through our webhook/send functions — this
# table gives Muna and admin a visible record of every
# conversation without needing to log into Meta Business Manager.

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime, timezone
from app.database.connection import Base


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id           = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    # The customer/fisher's number (not MarineCatch's)

    direction    = Column(String(10), nullable=False)
    # inbound, outbound

    message_text = Column(Text, nullable=True)
    button_id    = Column(String(50), nullable=True)
    # If the message was a button click

    sender_name  = Column(String(100), nullable=True)
    # Resolved name if the number matches a registered user

    user_role    = Column(String(20), nullable=True)
    # fisher, buyer, unknown — at time of message

    created_at   = Column(DateTime(timezone=True),
                          default=lambda: datetime.now(timezone.utc), index=True)