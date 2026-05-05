# Architecture

## Runtime Layout

```text
Internet / TLS edge
  |
  v
Host Caddy or equivalent TLS reverse proxy :443
  |
  v
Compose Nginx edge 127.0.0.1:8080
  |-- hypervaults.io/                   -> frontend:3000
  |-- hypervaults.io/api/               -> backend:8000
  |-- hypervaults.io/minio/             -> minio:9000, GET/HEAD only
  |-- hypervaults.io/objects/           -> minio:9000, GET/HEAD only, challenge mode
  |-- mailpit.hypervaults.io/mailpit/   -> mailpit:8025, Basic Auth, read-only methods
  |-- registry.hypervaults.io/          -> host Harbor on 8090, optional
```

## Docker Networks

- `edge`: Nginx host-facing edge.
- `app-net`: Nginx, frontend, backend, Mailpit. Marked `internal`.
- `data-net`: backend, PostgreSQL, MinIO, MinIO init, and Nginx for object downloads. Marked `internal`.

PostgreSQL, backend, frontend, Mailpit SMTP, and MinIO API are not published directly to the host. MinIO console is bound to `127.0.0.1:9001` for organizers only.

## Intentional Vulnerabilities

- Nginx challenge config forwards user-controlled `X-Forwarded-For` only for `/api/docs`, `/api/redoc`, and `/api/openapi.json`.
- FastAPI trusts spoofed localhost forwarding headers only when `ENABLE_X_FORWARDED_DOCS_BYPASS=true`.
- `TRACE /api/diagnostics/mail` is registered only when `ENABLE_TRACE_MAIL_DIAGNOSTICS=true`.
- Mailpit is exposed only through Nginx challenge routing, with Basic Auth and read-only method filtering.
- MinIO anonymous public read/list policy is applied only when `ENABLE_PUBLIC_MINIO_BUCKET=true`.
- `/objects/` allows only `GET` and `HEAD`, so players can read public objects but cannot write or delete them.
- Harbor is optional and should be disposable. The intended flaw is weak bootstrap credentials plus a leaked staging debug image.

## Shared-Service Safety

Mailpit UI/API traffic through Nginx allows `GET`, `HEAD`, and `OPTIONS` only. This prevents normal player workflows from deleting shared seeded messages. The backend also checks Mailpit every 10 seconds and re-sends any missing seeded challenge messages. If organizers expose Mailpit's raw port manually, the Nginx safeguard is bypassed, but the reseed loop still restores missing seed emails.

MinIO public exposure is read/list only through bucket policy and Nginx method filtering. Player uploads through the app still require authentication and ownership checks, but the public bucket challenge intentionally makes object contents readable.

Harbor should be treated as a disposable challenge service. Do not use global admin credentials outside this lab. For an event, seed only the `hypervaults/hypervaults-api:staging-debug` artifact and reset Harbor after the workshop.
