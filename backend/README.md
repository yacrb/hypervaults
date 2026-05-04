# HyperVaults Backend

FastAPI service for authentication, Turnstile verification, metadata persistence, and private MinIO object access.

## Responsibilities

- Hash passwords with Argon2 via `pwdlib`.
- Issue JWT access tokens signed with `JWT_SECRET`.
- Verify Cloudflare Turnstile tokens server-side on signup and login.
- Store user and file metadata in PostgreSQL with SQLAlchemy.
- Store file bytes in a private MinIO bucket under per-user object keys.
- Verify `owner_id` before file metadata lookup, download URL creation, or delete.

## Local Run

The recommended path is the root Compose stack:

```bash
cd ..
cp .env.example .env
docker compose up --build
```

For Postgres 18+, Compose mounts the database volume at `/var/lib/postgresql`. If an older local `hypervaults_postgres-data` volume exists from a prior run, remove that stale volume before restarting the stack.

For direct backend development, provide the same environment variables listed in `.env.example`, install requirements, then run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Direct `--reload` is for local editing only. The Docker image runs without debug reload.

## API Routes

- `GET /api/health`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/files/upload`
- `GET /api/files`
- `GET /api/files/{file_id}`
- `GET /api/files/{file_id}/download`
- `DELETE /api/files/{file_id}`
- `GET /api/docs` guarded manual docs route
- `GET /api/openapi.json` guarded manual OpenAPI route
- `GET /api/redoc` guarded manual ReDoc route

## Upload Policy

Allowed extensions and content types:

- `.txt` -> `text/plain`
- `.pdf` -> `application/pdf`
- `.png` -> `image/png`
- `.jpg` / `.jpeg` -> `image/jpeg`

The backend enforces max upload size, sanitizes filenames, checks declared content type, and performs a lightweight signature check for the supported starter set.

## Security Notes

- API docs are disabled with `docs_url=None`, `redoc_url=None`, and `openapi_url=None`.
- Manual docs routes are guarded by a localhost check and are blocked by the default Nginx config.
- CORS allows only local frontend origins.
- The backend never trusts a client-provided user ID.
- MinIO credentials are read from environment variables and never returned by API responses.
- Download URLs expire after 5 minutes and are generated only after ownership validation.
- Tables are created on startup for this first milestone. Alembic is the intended next step for migrations.

## X-Forwarded-For Docs Bypass Challenge

The backend has two challenge flags:

```env
CHALLENGE_MODE=false
ENABLE_X_FORWARDED_DOCS_BYPASS=false
```

With `ENABLE_X_FORWARDED_DOCS_BYPASS=false`, docs access checks only `request.client.host` and does not trust `X-Forwarded-For`.

With `ENABLE_X_FORWARDED_DOCS_BYPASS=true`, the docs guard intentionally trusts `X-Forwarded-For` values of `127.0.0.1` or `::1`. This is deliberately vulnerable and should be used only with `nginx/nginx.conf.challenge` for the first challenge branch.
