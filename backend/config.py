"""
Centralised configuration — all env vars loaded here via Pydantic Settings.
Never import os.environ directly elsewhere; use `from config import settings`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic
    anthropic_api_key: str

    # Database
    database_url: str  # postgresql+asyncpg://...

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    # Alerts
    sendgrid_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    teacher_alert_email: str = "teacher@school.example.com"

    # OCR
    google_vision_api_key: str = ""  # Optional; Tesseract used if empty

    # Object storage (Cloudflare R2 / S3-compatible)
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "studyowl-uploads"
    r2_endpoint: str = ""

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Session escalation thresholds
    max_fails_before_alert: int = 3
    inactivity_timeout_minutes: int = 10


settings = Settings()
