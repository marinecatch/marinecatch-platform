# app/api/v1/routes/users.py
from time import timezone

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
from app.core.security import verify_password, create_token, decode_token, hash_password
from app.schemas.user import validate_password_strength
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

router   = APIRouter(prefix="/api/v1/users", tags=["Users"])
security = HTTPBearer()

# Roles the public /register endpoint is allowed to create.
# Everything else (admin, coordinator, partner) must be created
# through an authenticated admin action, never self-service.
PUBLIC_REGISTRATION_ROLES = {"fisher", "supplier", "buyer"}

@router.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if user.role not in PUBLIC_REGISTRATION_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Public registration only supports these roles: {', '.join(PUBLIC_REGISTRATION_ROLES)}. Contact an administrator for other account types."
        )
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
    if user.account_status != "active":
        raise HTTPException(status_code=403, detail="This account is not active. Contact MarineCatch support.")
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

class AccountStatusUpdate(BaseModel):
    account_status: str  # "active" | "suspended" | "archived"


@router.patch("/{user_id}/status")
def update_account_status(
    user_id: int,
    payload: AccountStatusUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Suspend, reactivate, or archive a user account. Admin only."""
    admin_payload = decode_token(credentials.credentials)
    if not admin_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    admin_user = get_user_by_id(db, admin_payload["user_id"])
    if not admin_user or admin_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if payload.account_status not in ("active", "suspended", "archived"):
        raise HTTPException(status_code=400, detail="Invalid status. Use: active, suspended, archived")

    target = get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.account_status = payload.account_status
    db.commit()

    return {
        "id": target.id,
        "name": target.name,
        "email": target.email,
        "account_status": target.account_status,
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
        "is_ceo":        user.is_ceo,
        "account_status": user.account_status,
        "created_at":    user.created_at,
    }

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
@router.get("/")
def list_users(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    from app.models.user import User
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id":            u.id,
            "name":          u.name,
            "email":         u.email,
            "phone":         u.phone,
            "role":          u.role,
            "location":      u.location,
            "business_name": u.business_name,
            "is_active":     u.is_active,
            "is_ceo":        u.is_ceo,
            "is_lead":       u.is_lead,
            "created_at":    u.created_at,
            "lead_status":       u.lead_status,
            "lead_source":       u.lead_source,
            "assigned_to":       u.assigned_to,
            "lead_notes":        u.lead_notes,
            "last_contacted_at": u.last_contacted_at,
        }
        for u in users
    ]
    
# ── LEAD CAPTURE ──────────────────────────────────────────────────

class LeadCreate(BaseModel):
    name:     str
    phone:    str
    email:    Optional[str] = None
    role:     str
    location: Optional[str] = None
    message:  Optional[str] = None
    utm_source:  Optional[str] = None
    utm_medium:  Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term:         Optional[str] = None
    utm_content:      Optional[str] = None
    partner_code:     Optional[str] = None
    referrer:         Optional[str] = None
    landing_page:     Optional[str] = None
    device:           Optional[str] = None

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
    business_name = f"{payload.role} | src:{payload.utm_source or 'direct'} | med:{payload.utm_medium or 'none'} | camp:{payload.utm_campaign or 'none'} | {payload.message or ''}"[:200],
    is_active       = True,
    is_lead         = True,
)
    db.add(lead)
    # Save lead attribution
    from app.models.lead_attribution import LeadAttribution
    attribution = LeadAttribution(
        lead_name           = payload.name,
        lead_phone          = payload.phone,
        lead_email          = payload.email,
        lead_role           = payload.role,
        lead_location       = payload.location,
        lead_message        = payload.message,
        utm_source          = payload.utm_source or "direct",
        utm_medium          = payload.utm_medium or "none",
        utm_campaign        = payload.utm_campaign,
        utm_term            = payload.utm_term,
        utm_content         = payload.utm_content,
        partner_code        = payload.partner_code,
        referrer            = payload.referrer,
        landing_page        = payload.landing_page,
        device              = payload.device,
        registration_source = "website",
        first_visit         = datetime.now(timezone.utc),
    )
    db.add(attribution)
    db.commit()

    # AI lead qualification — score for sales prioritization
    try:
        from app.services.lead_qualification_service import score_lead
        scoring = score_lead(
            name=payload.name, role=payload.role,
            location=payload.location, message=payload.message,
        )
        lead.lead_notes = (
            f"AI Score: {scoring['score']}/10 ({scoring['priority']} priority) "
            f"— {scoring['reason']}"
        )
        db.commit()
    except Exception as e:
        print(f"Lead qualification failed: {e}")

    return {
        "success": True,
        "message": "Registration received. Our team will contact you within 24 hours on WhatsApp."
    }
# ── LEAD PIPELINE MANAGEMENT ──────────────────────────────────────

class LeadUpdate(BaseModel):
    lead_status: Optional[str] = None
    assigned_to: Optional[str] = None
    lead_notes:  Optional[str] = None

@router.post("/leads/{user_id}/update")
def update_lead(
    user_id:     int,
    payload:     LeadUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Update lead pipeline status, assignment, and notes."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    from app.models.user import User
    from datetime import datetime, timezone

    lead = db.query(User).filter(User.id == user_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.lead_status is not None:
        lead.lead_status = payload.lead_status
        lead.last_contacted_at = datetime.now(timezone.utc)
    if payload.assigned_to is not None:
        lead.assigned_to = payload.assigned_to
    if payload.lead_notes is not None:
        lead.lead_notes = payload.lead_notes

    db.commit()
    return {"success": True, "lead_status": lead.lead_status}

class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/me/change-password")
def change_password(
    payload: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Self-service password change. Requires the current password."""
    token_payload = decode_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, token_payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    try:
        validate_password_strength(payload.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


class DeactivateAccount(BaseModel):
    password: str  # confirm identity before deactivating — no accidental clicks


@router.post("/me/deactivate")
def deactivate_my_account(
    payload: DeactivateAccount,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Self-service account deactivation. Distinct from admin suspension."""
    token_payload = decode_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, token_payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Password is incorrect")

    user.account_status = "self_deactivated"
    db.commit()
    return {"message": "Account deactivated. Contact support to reactivate."}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    business_name: Optional[str] = None
    age: Optional[int] = None


@router.patch("/me")
def update_my_profile(
    payload: ProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Self-service profile edit. Deliberately excludes email, role, and
    anything security/permission-related — those need separate, more
    careful handling, not a generic profile form."""
    token_payload = decode_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, token_payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.name is not None:
        user.name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.location is not None:
        user.location = payload.location
    if payload.business_name is not None:
        user.business_name = payload.business_name
    if payload.age is not None:
        user.age = payload.age

    db.commit()
    db.refresh(user)

    return {
        "id": user.id, "name": user.name, "phone": user.phone,
        "location": user.location, "business_name": user.business_name,
        "age": user.age,
    }