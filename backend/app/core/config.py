from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_DATABASE_URL = "postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow"
DEVELOPMENT_SECRET_KEY = "development-only-change-me-at-least-32-bytes"
# Values that are public in this repository and must never sign production tokens.
PUBLIC_SECRET_KEYS = {DEVELOPMENT_SECRET_KEY, "replace-with-a-long-random-secret"}
MIN_SECRET_KEY_BYTES = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ClientFlow API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = DEVELOPMENT_DATABASE_URL
    secret_key: SecretStr = SecretStr(DEVELOPMENT_SECRET_KEY)
    access_token_expire_minutes: int = Field(default=60, gt=0)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    cors_origins: str = "http://localhost:5173"

    demo_user_email: str = "demo@clientflow.app"
    demo_user_password: SecretStr = SecretStr("development-only-change-me")
    demo_user_full_name: str = "ClientFlow Demo"
    demo_business_name: str = "ClientFlow Demo Company"
    demo_business_address: str = "123 Demo Street, Dhaka"
    demo_business_phone: str = "+880 1700-000000"
    demo_currency_code: str = "BDT"
    demo_timezone: str = "Asia/Dhaka"

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        return value

    @field_validator("demo_user_email")
    @classmethod
    def normalize_demo_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("DEMO_USER_EMAIL must be a valid email address")
        return normalized

    @field_validator("demo_currency_code")
    @classmethod
    def normalize_currency_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("DEMO_CURRENCY_CODE must be a three-letter code")
        return normalized

    @field_validator("demo_timezone")
    @classmethod
    def validate_demo_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("DEMO_TIMEZONE must be a valid IANA timezone") from error
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment != "production":
            return self

        secret_key = self.secret_key.get_secret_value()
        if (
            secret_key in PUBLIC_SECRET_KEYS
            or len(secret_key.encode("utf-8")) < MIN_SECRET_KEY_BYTES
        ):
            raise ValueError(
                f"SECRET_KEY must be a private value of at least {MIN_SECRET_KEY_BYTES} bytes "
                "in production"
            )
        if self.database_url == DEVELOPMENT_DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured in production")
        origins = self.cors_origin_list
        if not origins or "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
