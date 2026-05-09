# app/api/v1/routes/users.py
#
# WHY THIS FILE EXISTS:
# Handles user registration and login.
# Login returns a JWT token — every protected endpoint needs it.
#
# Real users:
# Abdalla Masudi registers as fisher (Kibuyuni)
# Neptune Hotels registers as buyer (Diani)

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.database.memory_store import (
    create_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id
)
from app.core.security import (
    hash_password,
    verify_password,
    create_token,
    decode_token
)

router   = APIRouter(prefix="/api/v1/users", tags=["Users"])
security = HTTPBearer()

# ── REGISTER ──────────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(user: UserCreate):
    """
    Register a new user.

    Examples:
    - Abdalla Masudi registers as fisher in Kibuyuni
    - Neptune Hotels registers as buyer in Diani
    - Juma Riziki registers as supplier in Kinondo
    """
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = create_user({
        "name":            user.name,
        "email":           user.email,
        "phone":           user.phone,
        "role":            user.role,
        "location":        user.location,
        "business_name":   user.business_name,
        "hashed_password": hash_password(user.password)
    })

    # Never return the password
    return {k: v for k, v in new_user.items()
            if k != "hashed_password"}

# ── LOGIN ─────────────────────────────────────────────────────────
@router.post("/login")
def login(credentials: UserLogin):
    """
    Login and receive JWT token.
    Include token in all protected requests:
    Header: Authorization: Bearer <token>
    """
    user = get_user_by_email(credentials.email)

    if not user or not verify_password(
        credentials.password, user["hashed_password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create token with user identity baked in
    token = create_token({
        "user_id":  user["id"],
        "email":    user["email"],
        "role":     user["role"],
        "name":     user["name"],
        "location": user.get("location")
    })

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":            user["id"],
            "name":          user["name"],
            "email":         user["email"],
            "role":          user["role"],
            "location":      user.get("location"),
            "business_name": user.get("business_name")
        }
    }

# ── GET CURRENT USER (from token) ─────────────────────────────────
@router.get("/me")
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Returns the logged-in user's profile.
    Requires: Authorization: Bearer <token>
    """
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return {k: v for k, v in user.items()
            if k != "hashed_password"}

# ── LIST ALL USERS (admin only later) ─────────────────────────────
@router.get("/")
def list_users():
    """
    List all users.
    Will be admin-only in Day 9.
    """
    return [
        {k: v for k, v in u.items() if k != "hashed_password"}
        for u in get_all_users()
    ]


# ── DEPENDENCY — use this in any protected route ──────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Reusable dependency for protected endpoints.

    Usage in any route:
    def my_endpoint(current_user = Depends(get_current_user)):

    Returns the full user dict if token is valid.
    Raises 401 if token is missing, invalid, or expired.
    """
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token. Please login again."
        )

    user = get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found"
        )

    return user