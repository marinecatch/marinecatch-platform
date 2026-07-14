# app/models/custody_event.py
#
# WHY THIS FILE EXISTS:
# Chain of custody — every handoff of a lot or shipment is
# recorded permanently. Strengthens traceability, supports
# dispute resolution and insurance claims, and lays the
# groundwork for future blockchain anchoring.

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from app.database.connection import Base


class CustodyEvent(Base):
    __tablename__ = "custody_events"

    id                  = Column(Integer, primary_key=True, index=True)
    lot_id              = Column(Integer, ForeignKey("inventory_lots.id"), nullable=True)
    transport_job_id    = Column(Integer, ForeignKey("transport_jobs.id"), nullable=True)

    from_party          = Column(String(150), nullable=True)
    to_party            = Column(String(150), nullable=True)

    event_type          = Column(String(30), nullable=True)
    # collected, inspected, stored, loaded, delivered, returned

    location            = Column(String(150), nullable=True)
    condition_notes      = Column(Text, nullable=True)
    photo_url            = Column(String(500), nullable=True)

    recorded_by         = Column(String(100), nullable=True)
    event_at            = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))

    created_at           = Column(DateTime(timezone=True),
                                  default=lambda: datetime.now(timezone.utc))