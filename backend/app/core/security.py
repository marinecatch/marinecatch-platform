from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict, expires_minutes: int = 1440) -> str:
    payload = {
        **data,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
    except JWTError:
        return None