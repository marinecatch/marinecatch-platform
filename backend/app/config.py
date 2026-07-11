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
    # KCB Buni API — bank transfer for large B2B payments
    # Architecture ready; credentials pending KCB partnership agreement
    KCB_ENVIRONMENT: str = "sandbox"
    KCB_CONSUMER_KEY: str = ""
    KCB_CONSUMER_SECRET: str = ""
    KCB_ACCOUNT_NUMBER: str = ""
    KCB_PAYBILL_NUMBER: str = ""
    KCB_CALLBACK_URL: str = "https://api.marinecatchafrica.com/api/v1/payments/kcb/callback"
    KCB_VALIDATION_URL: str = "https://api.marinecatchafrica.com/api/v1/payments/kcb/validate"
    KCB_CONFIRMATION_URL: str = "https://api.marinecatchafrica.com/api/v1/payments/kcb/confirm"
    # WhatsApp
    WHATSAPP_TOKEN:            str = ""
    WHATSAPP_PHONE_NUMBER_ID:  str = ""
    WHATSAPP_VERIFY_TOKEN:     str = "marinecatch_verify_2026"
    WHATSAPP_API_VERSION:      str = "v19.0"
    # Anthropic AI
    ANTHROPIC_API_KEY: str = ""
    # Africa's Talking
    AT_API_KEY:        str = ""
    AT_USERNAME:       str = "sandbox"
    AT_USSD_SHORTCODE: str = "*384*71253#"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"

settings = Settings()