# app/models/logistics_exception.py
#
# WHY THIS FILE EXISTS:
# Failures are first-class events, not phone calls that
# disappear. Bus breakdowns, delays, cooler damage, and
# temperature breaches all get recorded and tracked to
# resolution — building the data needed for partner
# performance scorecards later.

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from app.database.connection import Base


class LogisticsException(Base):
    __tablename__ = "logistics_exceptions"

    id                   = Column(Integer, primary_key=True, index=True)
    transport_job_id     = Column(Integer, ForeignKey("transport_jobs.id"), nullable=True)

    exception_type       = Column(String(30), nullable=True)
    # breakdown, delay, damage, temp_breach, lot_rejected,
    # recipient_unavailable, quantity_mismatch

    severity             = Column(String(20), default="medium")
    # low, medium, high, critical

    description          = Column(Text, nullable=True)

    resolution_status    = Column(String(20), default="open")
    # open, in_progress, resolved, escalated
    resolution_notes      = Column(Text, nullable=True)

    reported_at          = Column(DateTime(timezone=True),
                                  default=lambda: datetime.now(timezone.utc))
    resolved_at          = Column(DateTime(timezone=True), nullable=True)

    reported_by          = Column(String(100), nullable=True)