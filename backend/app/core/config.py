"""
SecureNet One - Application Configuration
Loads settings from environment variables / .env file using Pydantic Settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "SecureNet One"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://securenet:securenet@localhost:5432/securenet"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT Authentication ───────────────────────────────────────
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production-immediately"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # ── WireGuard ────────────────────────────────────────────────
    WG_SERVER_ENDPOINT: str = "127.0.0.1:51820"
    WG_SERVER_PUBLIC_KEY: str = ""
    WG_SERVER_PRIVATE_KEY: str = ""
    WG_SUBNET: str = "10.0.0.0/24"
    WG_DNS: str = "10.0.0.1"
    WG_INTERFACE: str = "wg0"

    # ── DNS-over-HTTPS ───────────────────────────────────────────
    DOH_UPSTREAM: str = "https://1.1.1.1/dns-query"
    DOH_ENABLE_LOGGING: bool = True
    DOH_ENABLE_FILTERING: bool = True

    # ── Device Heartbeat ─────────────────────────────────────────
    HEARTBEAT_INTERVAL_SECONDS: int = 60
    DEVICE_OFFLINE_THRESHOLD_SECONDS: int = 180


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
