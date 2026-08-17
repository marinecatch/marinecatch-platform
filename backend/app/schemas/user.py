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

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re

class UserRole(str, Enum):
    FISHER   = "fisher"      # Individual fishermen at landing sites
    SUPPLIER = "supplier"    # Fish traders and aggregators
    BUYER    = "buyer"       # Hotels, restaurants, wholesalers
    ADMIN    = "admin"       # MarineCatch staff

def validate_password_strength(v: str) -> str:
    if not re.search(r'[A-Za-z]', v):
        raise ValueError('Password must contain at least one letter')
    if not re.search(r'[0-9]', v):
        raise ValueError('Password must contain at least one number')
    return v

class UserCreate(BaseModel):
    name:     str      = Field(min_length=2, max_length=100)
    email:    EmailStr
    phone:    str      = Field(min_length=9, max_length=15)
    password: str      = Field(min_length=8)
    role:     UserRole = UserRole.FISHER

    @field_validator('password')
    @classmethod
    def check_password_strength(cls, v):
        return validate_password_strength(v)
    location: Optional[str] = None   # e.g. "Kibuyuni", "Diani", "Nairobi"
    business_name: Optional[str] = None  # e.g. "Neptune Hotels", "Rasa Fish Traders"
    age: Optional[int] = None  # e.g. 25, 30, 35

class UserResponse(BaseModel):
    id:            int
    name:          str
    email:         str
    phone:         str
    role:          UserRole
    location:      Optional[str]
    business_name: Optional[str]
    age: Optional[int] = None  # e.g. 25, 30, 35
    is_active:     bool
    created_at:    datetime

    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email:    EmailStr
    password: str