# app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

# Points to .env file in the same folder as config.py
ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "MarineCatch Africa API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "marinecatch-dev-secret-change-in-production"
    DATABASE_URL: str = "postgresql://marinecatch_user:devpassword123@localhost:5432/marinecatch_db"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"

settings = Settings()