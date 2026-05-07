from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

# Temporary in-memory storage
users_db = []

@router.post("/")
def create_user(name: str, role: str):
    user = {
        "id": len(users_db) + 1,
        "name": name,
        "role": role
    }
    users_db.append(user)
    return user

@router.get("/")
def get_users():
    return users_db