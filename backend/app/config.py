# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "MarineCatch Africa API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "marinecatch-dev-secret-change-in-production"

    # Database — SQLite now, PostgreSQL later
    DATABASE_URL: str = "sqlite:///./marinecatch.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()