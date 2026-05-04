from __future__ import annotations

import io
import re
import uuid
from datetime import timedelta
from pathlib import PurePath
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile, status
from minio import Minio

from app.config import get_settings


settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

DOWNLOAD_URL_TTL_SECONDS = 300


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password.get_secret_value(),
        secure=False,
    )


def ensure_bucket_exists() -> None:
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def sanitize_filename(filename: str) -> str:
    basename = PurePath(filename).name
    basename = basename.replace("\x00", "")
    stem, dot, extension = basename.rpartition(".")
    if not dot:
        stem = basename
        extension = ""

    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    safe_extension = re.sub(r"[^A-Za-z0-9]+", "", extension).lower()
    if not safe_stem:
        safe_stem = "file"

    safe_name = f"{safe_stem}.{safe_extension}" if safe_extension else safe_stem
    return safe_name[:180]


def validate_content_signature(extension: str, content: bytes) -> bool:
    if extension == ".pdf":
        return content.startswith(b"%PDF-")
    if extension == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if extension == ".txt":
        return b"\x00" not in content
    return False


async def read_and_validate_upload(upload: UploadFile) -> tuple[str, bytes, str]:
    safe_name = sanitize_filename(upload.filename or "file")
    extension = f".{safe_name.rsplit('.', 1)[-1].lower()}" if "." in safe_name else ""
    expected_content_type = ALLOWED_CONTENT_TYPES.get(extension)
    if expected_content_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File extension is not allowed")

    supplied_content_type = (upload.content_type or "").split(";", 1)[0].strip().lower()
    if supplied_content_type != expected_content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content type is not allowed")

    content = await upload.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds upload size limit")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty files are not supported")
    if not validate_content_signature(extension, content):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content does not match its declared type")

    return safe_name, content, expected_content_type


def object_key_for_user(user_id: uuid.UUID, filename: str) -> str:
    return f"users/{user_id}/{uuid.uuid4()}-{filename}"


def upload_object(object_key: str, content: bytes, content_type: str) -> None:
    client = get_minio_client()
    client.put_object(
        settings.minio_bucket,
        object_key,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type,
    )


def remove_object(object_key: str) -> None:
    client = get_minio_client()
    client.remove_object(settings.minio_bucket, object_key)


def presigned_download_url(object_key: str) -> str:
    client = get_minio_client()
    internal_url = client.presigned_get_object(
        settings.minio_bucket,
        object_key,
        expires=timedelta(seconds=DOWNLOAD_URL_TTL_SECONDS),
    )
    parsed = urlparse(internal_url)
    public_base = str(settings.minio_presigned_public_base_url).rstrip("/")
    return f"{public_base}{parsed.path}?{parsed.query}"
