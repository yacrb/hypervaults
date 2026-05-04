from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.security import create_access_token, hash_password, verify_password
from app.turnstile import verify_turnstile_token


router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def token_response_for(user: models.User) -> schemas.TokenResponse:
    return schemas.TokenResponse(
        access_token=create_access_token(user.id, user.email),
        expires_in_seconds=settings.access_token_expire_minutes * 60,
    )


@router.post("/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: schemas.SignupRequest, request: Request, db: Session = Depends(get_db)) -> schemas.TokenResponse:
    await verify_turnstile_token(payload.turnstile_token, request.client.host if request.client else None)

    email = payload.email.lower()
    existing_user = db.scalar(select(models.User).where(models.User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = models.User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc
    db.refresh(user)
    return token_response_for(user)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(payload: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)) -> schemas.TokenResponse:
    await verify_turnstile_token(payload.turnstile_token, request.client.host if request.client else None)

    email = payload.email.lower()
    user = db.scalar(select(models.User).where(models.User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return token_response_for(user)


@router.get("/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user
