# app/api/v1/routes/users.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin
from app.database.connection import get_db
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_all_users
)
from app.core.security import verify_password, create_token, decode_token
from pydantic import BaseModel

router   = APIRouter(prefix="/api/v1/users", tags=["Users"])
security = HTTPBearer()

@router.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    new_user = create_user(
        db=            db,
        name=          user.name,
        email=         user.email,
        phone=         user.phone,
        password=      user.password,
        role=          user.role,
        location=      user.location,
        business_name= user.business_name
    )
    return {
        "id":            new_user.id,
        "name":          new_user.name,
        "email":         new_user.email,
        "phone":         new_user.phone,
        "role":          new_user.role,
        "location":      new_user.location,
        "business_name": new_user.business_name,
        "is_active":     new_user.is_active,
        "created_at":    new_user.created_at,
    }

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token({
        "user_id":  user.id,
        "email":    user.email,
        "role":     user.role,
        "name":     user.name,
        "location": user.location
    })
    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":            user.id,
            "name":          user.name,
            "email":         user.email,
            "role":          user.role,
            "location":      user.location,
            "business_name": user.business_name
        }
    }

@router.get("/me")
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id":            user.id,
        "name":          user.name,
        "email":         user.email,
        "phone":         user.phone,
        "role":          user.role,
        "location":      user.location,
        "business_name": user.business_name,
        "is_active":     user.is_active,
        "created_at":    user.created_at,
    }

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return [
        {"id": u.id, "name": u.name, "email": u.email,
         "role": u.role, "location": u.location}
        for u in users
    ]

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User account not found")
    return user
    
# ── LEAD CAPTURE ──────────────────────────────────────────────────

class LeadCreate(BaseModel):
    name:     str
    phone:    str
    email:    Optional[str] = None
    role:     str
    location: Optional[str] = None
    message:  Optional[str] = None

@router.post("/leads", status_code=201, tags=["Leads"])
def capture_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    """
    Capture lead from landing page registration form.
    Stores as inactive user for follow-up.
    No authentication required.
    """
    from app.models.user import User
    from passlib.context import CryptContext
    import secrets

    # Check if phone already registered
    existing = db.query(User).filter(
        User.phone.contains(payload.phone[-9:])
    ).first()

    if existing:
        return {
            "success": True,
            "message": "Already registered. Our team will be in touch.",
            "existing": True
        }

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Map role to system role
    role_map = {
        "fisher":           "fisher",
        "supplier":         "fisher",
        "buyer_hotel":      "buyer",
        "buyer_restaurant": "buyer",
        "processor":        "buyer",
        "logistics":        "buyer",
        "bmu":              "fisher",
        "investor":         "buyer",
        "other":            "buyer",
    }
    system_role = role_map.get(payload.role, "buyer")

    lead = User(
    name            = payload.name,
    phone           = payload.phone,
    email           = payload.email or f"lead_{secrets.token_hex(4)}@marinecatch.co.ke",
    hashed_password = pwd.hash(secrets.token_hex(16)),
    role            = system_role,
    location        = payload.location or "",
    business_name   = f"{payload.role}: {payload.message or ''}"[:200],
    is_active       = False,
)
    db.add(lead)
    db.commit()

    return {
        "success": True,
        "message": "Registration received. Our team will contact you within 24 hours on WhatsApp."
    }