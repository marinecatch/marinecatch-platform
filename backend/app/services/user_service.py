# app/services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.user import User
from app.core.security import hash_password

def create_user(db: Session, name: str, email: str, phone: str,
                password: str, role: str, location: str = None,
                business_name: str = None) -> User:
    db_user = User(
        name=            name,
        email=           email,
        phone=           phone,
        hashed_password= hash_password(password),
        role=            role,
        location=        location,
        business_name=   business_name,
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(User).filter(User.is_active == True).all()