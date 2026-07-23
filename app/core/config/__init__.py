"""SYQ application configuration."""

import json
import os
import secrets
from typing import List, Union

try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pydantic v1 fallback
    from pydantic import BaseSettings, Field, validator

    SettingsConfigDict = None  # type: ignore[misc, assignment]


def normalize_database_url(url: str) -> str:
    """Convert DATABASE_URL to async SQLAlchemy format."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///") and "aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


if SettingsConfigDict is not None:

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            case_sensitive=True,
            env_file=".env",
            extra="ignore",
        )

        PROJECT_NAME: str = "SYQ - Opportunity Intelligence Platform"
        VERSION: str = "0.1.0"
        DESCRIPTION: str = (
            "An intelligence layer above existing markets that helps users "
            "discover, evaluate, and act on valuable opportunities."
        )
        ENVIRONMENT: str = "development"

        API_V1_STR: str = "/api/v1"
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        DEBUG: bool = False

        SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
        ALGORITHM: str = "HS256"

        DATABASE_URL: str = "sqlite+aiosqlite:///./syq.db"
        DATABASE_ECHO: bool = False

        POSTGRES_SERVER: str = "localhost"
        POSTGRES_USER: str = "postgres"
        POSTGRES_PASSWORD: str = "password"
        POSTGRES_DB: str = "syq"
        POSTGRES_PORT: str = "5432"

        REDIS_HOST: str = "localhost"
        REDIS_PORT: int = 6379
        REDIS_URL: str = "redis://localhost:6379/0"

        BACKEND_CORS_ORIGINS: List[Union[str, str]] = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
        ALLOWED_HOSTS: List[str] = ["*"]

        RATE_LIMIT_PER_MINUTE: int = 60
        RATE_LIMIT_BURST: int = 10

        HSTS_MAX_AGE: int = 31536000
        CSP_POLICY: str = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        ENABLE_ANALYTICS: bool = True
        ENABLE_CACHING: bool = True

        @field_validator("BACKEND_CORS_ORIGINS", mode="before")
        @classmethod
        def parse_cors_origins(cls, value):
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    return [origin.strip() for origin in value.split(",") if origin.strip()]
            return value

        @field_validator("ALLOWED_HOSTS", mode="before")
        @classmethod
        def parse_allowed_hosts(cls, value):
            if isinstance(value, str):
                if value.strip() == "*":
                    return ["*"]
                return [host.strip() for host in value.split(",") if host.strip()]
            return value

        @property
        def async_database_url(self) -> str:
            env_database_url = os.getenv("DATABASE_URL")
            if env_database_url:
                return normalize_database_url(env_database_url)

            if self.DATABASE_URL and self.DATABASE_URL != "sqlite+aiosqlite:///./syq.db":
                return normalize_database_url(self.DATABASE_URL)

            if self.POSTGRES_SERVER not in ("localhost", "127.0.0.1"):
                built_url = (
                    f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                    f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                )
                return normalize_database_url(built_url)

            return normalize_database_url(self.DATABASE_URL)

else:

    class Settings(BaseSettings):
        PROJECT_NAME: str = "SYQ - Opportunity Intelligence Platform"
        VERSION: str = "0.1.0"
        API_V1_STR: str = "/api/v1"
        SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
        DATABASE_URL: str = "sqlite+aiosqlite:///./syq.db"
        BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
        ALLOWED_HOSTS: List[str] = ["*"]

        class Config:
            case_sensitive = True
            env_file = ".env"

        @property
        def async_database_url(self) -> str:
            env_database_url = os.getenv("DATABASE_URL")
            if env_database_url:
                return normalize_database_url(env_database_url)
            return normalize_database_url(self.DATABASE_URL)


settings = Settings()
