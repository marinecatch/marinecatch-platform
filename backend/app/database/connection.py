# app/database/connection.py
#
# WHY THIS FILE EXISTS:
# Manages the connection pool to PostgreSQL.
# Every API request gets its own database session.
# Session closes automatically when request finishes.
#
# get_db() is used as a dependency in routes:
# def my_endpoint(db: Session = Depends(get_db)):

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Create connection pool
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # Test connection before using
    echo=settings.DEBUG    # Log SQL queries in development
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class all models inherit from
class Base(DeclarativeBase):
    pass

def get_db():
    """
    One database session per request.
    Always closes after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()