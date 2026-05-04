import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    turnstile_token: str = Field(min_length=1, max_length=4096)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    turnstile_token: str = Field(min_length=1, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FileRead(BaseModel):
    id: uuid.UUID
    original_filename: str
    size_bytes: int
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int
