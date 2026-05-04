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

The default config also blocks `TRACE` and returns `404` for `/api/docs`, `/api/redoc`, and `/api/openapi.json`.

## Configs

- `nginx.conf`: secure default used by `.env.example`.
- `nginx.conf.secure`: explicit secure copy for comparison.
- `nginx.conf.challenge`: first challenge config.

To run the first challenge, set:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf.challenge
CHALLENGE_MODE=true
ENABLE_X_FORWARDED_DOCS_BYPASS=true
```

`nginx.conf.challenge` intentionally forwards the client-provided `X-Forwarded-For` header only for the docs endpoints. This is unsafe by design for the challenge. Regular API routes and MinIO download proxying remain scoped to their existing behavior.

## MinIO

The MinIO console is not proxied. It is exposed directly by Docker Compose on `http://localhost:9001` for local admin testing only.
