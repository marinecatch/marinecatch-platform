from fastapi import APIRouter, HTTPException

from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.database.memory_store import (
    create_user,
    get_all_users,
    get_user_by_email
)
from app.core.security import hash_password, verify_password

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# Get all users
@router.get("/", response_model=list[UserResponse])
def list_users():
    return get_all_users()


# Register new user
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):

    existing = get_user_by_email(user.email)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = create_user({
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "location": user.location,
        "business_name": user.business_name,
        "hashed_password": hash_password(user.password)
    })

    return new_user


# Login user
@router.post("/login")
def login(credentials: UserLogin):

    user = get_user_by_email(credentials.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    valid = verify_password(
        credentials.password,
        user["hashed_password"]
    )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": user["id"],
        "role": user["role"]
    }