from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.docs import openapi_description, register_docs_routes
from app.routes import auth, files, health
from app.storage import ensure_bucket_exists


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # First milestone convenience: create tables at startup.
    # TODO: Introduce Alembic migrations before this baseline is promoted beyond local development.
    Base.metadata.create_all(bind=engine)
    ensure_bucket_exists()
    yield


app = FastAPI(
    title="HyperVaults API",
    description=openapi_description(),
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(files.router)
register_docs_routes(app)
