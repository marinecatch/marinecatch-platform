# app/schemas/user.py
#
# WHY THIS FILE EXISTS:
# Defines exactly what user data looks like going IN and OUT.
# UserCreate = what someone sends when registering
# UserResponse = what we send back (NEVER includes password)
#
# Real roles based on MarineCatch operations:
# - fisher    → Abdalla Masudi, Bakari Usi (Kibuyuni)
# - supplier  → Juma Riziki (Kinondo), Said Mohamed (Shimoni)
# - buyer     → Neptune Hotels (Diani), Samaki Samaki (Nairobi)
# - admin     → MarineCatch operations team

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    FISHER   = "fisher"      # Individual fishermen at landing sites
    SUPPLIER = "supplier"    # Fish traders and aggregators
    BUYER    = "buyer"       # Hotels, restaurants, wholesalers
    ADMIN    = "admin"       # MarineCatch staff

class UserCreate(BaseModel):
    name:     str      = Field(min_length=2, max_length=100)
    email:    EmailStr
    phone:    str      = Field(min_length=9, max_length=15)
    password: str      = Field(min_length=8)
    role:     UserRole = UserRole.FISHER
    location: Optional[str] = None   # e.g. "Kibuyuni", "Diani", "Nairobi"
    business_name: Optional[str] = None  # e.g. "Neptune Hotels", "Rasa Fish Traders"

class UserResponse(BaseModel):
    id:            int
    name:          str
    email:         str
    phone:         str
    role:          UserRole
    location:      Optional[str]
    business_name: Optional[str]
    is_active:     bool
    created_at:    datetime

    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email:    EmailStr
    password: str