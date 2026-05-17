"""Application settings loaded from environment variables (.env)."""
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Application
    app_name: str = "EatWise"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'eatwise.db'}"

    # Security
    jwt_secret: str = "change-me-please-generate-a-strong-random-secret"
    jwt_algorithm: str = "HS256"
    # 24 hours during development; tighten to 15-60 min in production
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30

    # OTP
    otp_length: int = 6
    otp_expire_minutes: int = 5
    otp_max_attempts: int = 5
    otp_rate_limit_per_minute: int = 3

    # SMS gateway (optional)
    unifonic_app_sid: str = ""
    unifonic_sender_id: str = "EatWise"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,capacitor://localhost"

    # Storage
    storage_dir: str = str(BASE_DIR / "storage")
    max_upload_mb: int = 8

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Priority order (highest first):
          1. init arguments
          2. .env file  ← bumped above OS env so the project's local .env
             always wins over any pre-set OS variable (e.g., a system-wide
             DATABASE_URL pointing to MySQL from an unrelated project).
          3. OS environment variables
          4. secret files
        """
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sms_enabled(self) -> bool:
        return bool(self.unifonic_app_sid)


settings = Settings()
