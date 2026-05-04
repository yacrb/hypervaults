# HyperVaults

HyperVaults is a local development baseline for a modern secure document vault. Users can create an account, log in, upload approved private files, list only their own files, download only their own files, and delete only their own files.

This repository is the secure foundation. The intentionally vulnerable CTF branches are planned but are not implemented here.

## Architecture

```text
Browser
  |
  v
Nginx :80
  |-- /           -> Next.js frontend :3000
  |-- /api/       -> FastAPI backend :8000
  |-- /minio/     -> MinIO API :9000 for presigned GET/HEAD downloads only
  |
  |-- blocks /api/docs, /api/redoc, /api/openapi.json
  |-- does not proxy MinIO console

FastAPI
  |-- PostgreSQL stores users and file metadata
  |-- MinIO stores private file objects under users/{user_id}/...
  |-- Cloudflare Turnstile verifies signup/login tokens server-side

MinIO console is exposed directly at http://localhost:9001 for local admin testing only.
```

## Services

- `nginx`: reverse proxy on `http://localhost`
- `frontend`: Next.js App Router UI
- `backend`: FastAPI API under `/api`
- `postgres`: local PostgreSQL, Docker-network only
- `minio`: local private object storage, console on `localhost:9001`
- `minio-init`: one-shot bucket creation with private anonymous policy

## Setup

```bash
cd hypervaults
cp .env.example .env
docker compose up --build
```

Then open:

- App: http://localhost
- MinIO console: http://localhost:9001

The default `.env.example` uses Cloudflare Turnstile official dummy keys that always pass local validation. For real Turnstile credentials, replace both `NEXT_PUBLIC_TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`.

Cloudflare test key reference: https://developers.cloudflare.com/turnstile/troubleshooting/testing/

## Turnstile

Signup and login require a Turnstile token. The frontend renders a Turnstile widget, then the backend verifies the token with:

```text
POST https://challenges.cloudflare.com/turnstile/v0/siteverify
```

For local automated testing, the safer default is the official dummy key pair already in `.env.example`:

- Site key: `1x00000000000000000000AA`
- Secret key: `1x0000000000000000000000000000000AA`
- Dummy token for curl tests: `XXXX.DUMMY.TOKEN.XXXX`

An explicit bypass also exists for local development only:

```env
TURNSTILE_DEV_BYPASS=true
NEXT_PUBLIC_TURNSTILE_SITE_KEY=dev-bypass
```

When bypass is enabled, the backend accepts only the sentinel token `dev-bypass-token`. The bypass is disabled by default and is not silently applied.

## Local Test Commands

Run the stack:

```bash
docker compose up --build
```

Visit the app:

```text
http://localhost
```

Health check:

```bash
curl http://localhost/api/health
```

Signup:

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"CorrectHorseBatteryStaple!42","turnstile_token":"XXXX.DUMMY.TOKEN.XXXX"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Login:

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"CorrectHorseBatteryStaple!42","turnstile_token":"XXXX.DUMMY.TOKEN.XXXX"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Create and upload a file:

```bash
printf "HyperVaults local test\n" > sample.txt
curl -s -X POST http://localhost/api/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.txt;type=text/plain"
```

List files:

```bash
curl -s http://localhost/api/files \
  -H "Authorization: Bearer $TOKEN"
```

Download a file:

```bash
FILE_ID=$(curl -s http://localhost/api/files \
  -H "Authorization: Bearer $TOKEN" \
  | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

DOWNLOAD_URL=$(curl -s http://localhost/api/files/$FILE_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  | python -c "import sys,json; print(json.load(sys.stdin)['download_url'])")

curl -L "$DOWNLOAD_URL" -o downloaded-sample.txt
```

Delete a file:

```bash
curl -i -X DELETE http://localhost/api/files/$FILE_ID \
  -H "Authorization: Bearer $TOKEN"
```

On Windows PowerShell, use `curl.exe` if `curl` is aliased to `Invoke-WebRequest`.

## Security Baseline Checklist

- No public MinIO bucket.
- No leaked MinIO secret or JWT secret in the frontend.
- No backend debug dump endpoint.
- Swagger, ReDoc, and OpenAPI JSON are disabled in FastAPI and blocked by Nginx.
- TRACE is blocked by Nginx.
- File metadata, download, and delete routes filter by `owner_id`.
- Upload filenames are sanitized.
- Upload size, extensions, content types, and simple file signatures are restricted.
- JWT secret comes from the environment.
- Turnstile is verified server-side for signup and login.
- CORS is restricted to local frontend origins.
- MinIO console is not proxied through Nginx.

## Planned Future Vulnerable Branches

These branches are planned for later challenge work and are not implemented in this secure baseline:

1. MinIO public bucket exposure branch
2. Swagger/TRACE diagnostics branch
3. Resend support-email branch
4. Broken file authorization branch

## Development Notes

The backend uses `create_all` on startup for the first milestone to keep local setup simple. Alembic migrations should be introduced before this project is used beyond local development.
