# HyperVaults Nginx

Nginx is the single browser-facing entry point for local development.

## Routes

- `/` proxies to the Next.js frontend.
- `/api/` proxies to FastAPI and preserves the `/api` prefix.
- `/minio/` proxies only GET/HEAD requests to MinIO for presigned object downloads.

## Hardening

The config adds:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- restrictive `Permissions-Policy`

It also blocks `TRACE` and returns `404` for `/api/docs`, `/api/redoc`, and `/api/openapi.json`.

## MinIO

The MinIO console is not proxied. It is exposed directly by Docker Compose on `http://localhost:9001` for local admin testing only.
