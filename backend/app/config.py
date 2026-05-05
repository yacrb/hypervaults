from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret: SecretStr = Field(alias="JWT_SECRET", min_length=32)
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", ge=5, le=1440)

    minio_root_user: str = Field(alias="MINIO_ROOT_USER")
    minio_root_password: SecretStr = Field(alias="MINIO_ROOT_PASSWORD")
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_bucket: str = Field(default="hypervaults-files", alias="MINIO_BUCKET")
    minio_presigned_public_base_url: AnyHttpUrl = Field(
        default="http://localhost/minio",
        alias="MINIO_PRESIGNED_PUBLIC_BASE_URL",
    )

    turnstile_secret_key: SecretStr = Field(alias="TURNSTILE_SECRET_KEY")
    turnstile_dev_bypass: bool = Field(default=False, alias="TURNSTILE_DEV_BYPASS")

    challenge_mode: bool = Field(default=False, alias="CHALLENGE_MODE")
    enable_x_forwarded_docs_bypass: bool = Field(default=False, alias="ENABLE_X_FORWARDED_DOCS_BYPASS")

    # Second challenge branch: TRACE mail diagnostics + exposed Mailpit.
    # ENABLE_TRACE_MAIL_DIAGNOSTICS registers the TRACE /api/diagnostics/mail route
    # and seeds staging emails into Mailpit at startup.
    # ENABLE_MAILPIT_EXPOSURE is a documentation flag — actual Mailpit exposure is
    # controlled by the Nginx config selected via NGINX_CONFIG_FILE.
    enable_trace_mail_diagnostics: bool = Field(default=False, alias="ENABLE_TRACE_MAIL_DIAGNOSTICS")
    enable_mailpit_exposure: bool = Field(default=False, alias="ENABLE_MAILPIT_EXPOSURE")

    smtp_host: str = Field(default="mailpit", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_from: str = Field(default="HyperVaults Dev <no-reply@hypervaults.local>", alias="SMTP_FROM")
    mailpit_ui_public_url: str = Field(default="http://localhost/mailpit", alias="MAILPIT_UI_PUBLIC_URL")
    # INTENTIONAL CHALLENGE VULNERABILITY: these credentials are intentionally weak
    # and are exposed by the TRACE diagnostics endpoint when enabled.
    mailpit_basic_user: str = Field(default="devmail", alias="MAILPIT_BASIC_USER")
    mailpit_basic_password: str = Field(default="devmail2026", alias="MAILPIT_BASIC_PASSWORD")

    max_upload_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_UPLOAD_BYTES", ge=1, le=25 * 1024 * 1024)
    cors_allowed_origins: list[str] = ["http://localhost", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
