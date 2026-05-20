# app/models/shipment_event.py
#
# WHY THIS FILE EXISTS:
# Every status change and IoT reading for a shipment
# is recorded as an immutable event.
# This becomes the audit trail for delivery disputes,
# cold chain compliance, and ESG reporting.

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id           = Column(Integer, primary_key=True, index=True)
    shipment_id  = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)

    event_type   = Column(String(50), nullable=False)
    # status_change, iot_reading, cold_chain_breach,
    # driver_checkin, delivery_attempt, note

    event_detail = Column(String(200), nullable=True)
    # Human readable: "Status changed to in_transit"

    # IoT snapshot at time of event
    temperature_celsius = Column(Float, nullable=True)
    humidity_percent    = Column(Float, nullable=True)
    current_lat         = Column(Float, nullable=True)
    current_lng         = Column(Float, nullable=True)

    recorded_by  = Column(String(100), nullable=True)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    shipment = relationship("Shipment", foreign_keys=[shipment_id])

    def __repr__(self):
        return f"<ShipmentEvent {self.event_type} shipment={self.shipment_id}>"