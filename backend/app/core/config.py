# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Clinic AI Agent"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # GROQ
    GROQ_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = "./google_credentials.json"
    GOOGLE_SHEET_ID: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()