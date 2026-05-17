# app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    # App
    APP_NAME: str = "MarineCatch Africa API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "marinecatch-dev-secret-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://marinecatch_user:devpassword123@localhost:5432/marinecatch_db"

    # M-Pesa
    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_SHORTCODE: str = "174379"
    MPESA_PASSKEY: str = ""
    MPESA_ENVIRONMENT: str = "sandbox"
    MPESA_CALLBACK_URL: str = "https://localhost/api/v1/payments/mpesa/callback"
    MPESA_B2C_SHORTCODE: str = "174379"
    MPESA_INITIATOR_NAME: str = "testapi"
    MPESA_SECURITY_CREDENTIAL: str = ""

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"

settings = Settings()