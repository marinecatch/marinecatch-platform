# app/models/user.py
#
# WHY THIS FILE EXISTS:
# Defines the users table in PostgreSQL.
# Every fisher, buyer, supplier, admin is stored here.
#
# Real examples:
# Abdalla Masudi — fisher — Kibuyuni
# Neptune Hotels — buyer — Diani
# Juma Riziki    — supplier — Kinondo

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class UserRole(str, enum.Enum):
    FISHER   = "fisher"
    SUPPLIER = "supplier"
    BUYER    = "buyer"
    ADMIN    = "admin"

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    phone           = Column(String(20), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(SAEnum(UserRole), default=UserRole.FISHER, nullable=False)
    location        = Column(String(200), nullable=True)
    business_name   = Column(String(200), nullable=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships — one user can have many listings and orders
    listings = relationship("FishListing", back_populates="fisher")
    orders   = relationship("Order", back_populates="buyer",
                            foreign_keys="Order.buyer_id")

    def __repr__(self):
        return f"<User id={self.id} name={self.name} role={self.role}>"