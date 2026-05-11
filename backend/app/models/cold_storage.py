# app/models/cold_storage.py
#
# MarineCatch currently operates cold storage at:
# - Ukunda
# - Kinondo  
# - Kibuyuni
#
# This model tracks capacity, current usage, and costs.

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base


class ColdStorageFacility(Base):
    __tablename__ = "cold_storage_facilities"

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String(100), nullable=False)
    # "Ukunda Cold Storage", "Kinondo Hub", "Kibuyuni Landing Store"

    location         = Column(String(100), nullable=False)
    # Town/area name

    county           = Column(String(50), nullable=True)
    country          = Column(String(50), default="Kenya", nullable=False)

    # Capacity
    total_capacity_kg    = Column(Float, nullable=False)
    current_stock_kg     = Column(Float, default=0.0, nullable=False)
    # current_stock_kg updated as lots enter/exit

    temperature_min_c    = Column(Float, nullable=True)
    # Minimum temperature capability e.g. -18°C for frozen
    temperature_max_c    = Column(Float, nullable=True)
    # Maximum safe temperature e.g. 4°C for fresh

    # Fees
    storage_fee_per_kg_per_day = Column(Float, default=5.0)
    # Default 5 KES/kg/day — adjustable per facility

    # Contact
    manager_name     = Column(String(100), nullable=True)
    manager_phone    = Column(String(20), nullable=True)
    address          = Column(String(300), nullable=True)

    # Status
    is_active        = Column(Boolean, default=True, nullable=False)
    is_verified      = Column(Boolean, default=False, nullable=False)

    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ColdStorageFacility {self.name} capacity={self.total_capacity_kg}kg>"