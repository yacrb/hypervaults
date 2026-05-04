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
