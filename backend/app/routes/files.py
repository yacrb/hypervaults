from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.storage import (
    DOWNLOAD_URL_TTL_SECONDS,
    object_key_for_user,
    presigned_download_url,
    read_and_validate_upload,
    remove_object,
    upload_object,
)


router = APIRouter(prefix="/api/files", tags=["files"])
settings = get_settings()


def get_owned_file_or_404(file_id: UUID, owner_id: UUID, db: Session) -> models.StoredFile:
    stored_file = db.scalar(
        select(models.StoredFile).where(models.StoredFile.id == file_id, models.StoredFile.owner_id == owner_id)
    )
    if stored_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return stored_file


@router.post("/upload", response_model=schemas.FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile = File(..., alias="file"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.StoredFile:
    safe_name, content, content_type = await read_and_validate_upload(upload)
    object_key = object_key_for_user(current_user.id, safe_name)

    upload_object(object_key, content, content_type)
    stored_file = models.StoredFile(
        owner_id=current_user.id,
        original_filename=safe_name,
        stored_object_key=object_key,
        bucket=settings.minio_bucket,
        size_bytes=len(content),
        content_type=content_type,
    )
    db.add(stored_file)
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_object(object_key)
        raise
    db.refresh(stored_file)
    return stored_file


@router.get("", response_model=list[schemas.FileRead])
def list_files(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.StoredFile]:
    return list(
        db.scalars(
            select(models.StoredFile)
            .where(models.StoredFile.owner_id == current_user.id)
            .order_by(desc(models.StoredFile.created_at))
        )
    )


@router.get("/{file_id}", response_model=schemas.FileRead)
def get_file(
    file_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.StoredFile:
    return get_owned_file_or_404(file_id, current_user.id, db)


@router.get("/{file_id}/download", response_model=schemas.DownloadUrlResponse)
def download_file(
    file_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.DownloadUrlResponse:
    stored_file = get_owned_file_or_404(file_id, current_user.id, db)

    public_object_url = None
    if settings.enable_objects_gateway:
        # INTENTIONAL CHALLENGE VULNERABILITY (third branch):
        # Return a direct public object URL alongside the presigned URL.
        # This makes the open bucket beginner-discoverable: the player sees the
        # URL pattern, strips the filename, and browses to the bucket root to
        # find other files and the seeded flag.txt.
        base = settings.objects_public_base_url.rstrip("/")
        public_object_url = f"{base}/{settings.minio_bucket}/{stored_file.stored_object_key}"

    return schemas.DownloadUrlResponse(
        download_url=presigned_download_url(stored_file.stored_object_key),
        expires_in_seconds=DOWNLOAD_URL_TTL_SECONDS,
        public_object_url=public_object_url,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    stored_file = get_owned_file_or_404(file_id, current_user.id, db)
    remove_object(stored_file.stored_object_key)
    db.delete(stored_file)
    db.commit()
