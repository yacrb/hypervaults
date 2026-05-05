import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.docs import openapi_description, register_docs_routes
from app.mail import ensure_challenge_emails, reseed_challenge_emails_forever
from app.routes import auth, files, health
from app.storage import ensure_bucket_exists


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # First milestone convenience: create tables at startup.
    # TODO: Introduce Alembic migrations before this baseline is promoted beyond local development.
    Base.metadata.create_all(bind=engine)
    ensure_bucket_exists()

    reseed_task: asyncio.Task[None] | None = None

    # Keep shared challenge emails present whenever challenge mode is active.
    # The reseed check is idempotent and only sends messages missing from Mailpit.
    if settings.challenge_mode:
        ensure_challenge_emails()
        reseed_task = asyncio.create_task(reseed_challenge_emails_forever())

    try:
        yield
    finally:
        if reseed_task:
            reseed_task.cancel()
            with suppress(asyncio.CancelledError):
                await reseed_task


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

# INTENTIONAL CHALLENGE VULNERABILITY (second branch):
# The TRACE diagnostics router is only registered when the flag is enabled.
# In secure mode this route does not exist — it returns 404.
if settings.enable_trace_mail_diagnostics:
    from app.routes import diagnostics
    app.include_router(diagnostics.router)
