# HyperVaults

HyperVaults is a local development baseline for a modern secure document vault. Users can create an account, log in, upload approved private files, list only their own files, download only their own files, and delete only their own files.

The default configuration remains secure. Intentional challenges are opt-in via environment flags and the challenge Nginx config.

## Architecture

```text
Browser
  |
  v
Nginx :80
  |-- /           -> Next.js frontend :3000
  |-- /api/       -> FastAPI backend :8000
  |-- /minio/     -> MinIO API :9000 for presigned GET/HEAD downloads only
  |-- /mailpit/   -> Mailpit web UI :8025 (challenge mode only, with Basic Auth)
  |
  |-- blocks /api/docs, /api/redoc, /api/openapi.json by default
  |-- blocks TRACE by default
  |-- blocks /mailpit by default
  |-- can opt into the challenge config for both vulnerability branches
  |-- does not proxy MinIO console

FastAPI
  |-- PostgreSQL stores users and file metadata
  |-- MinIO stores private file objects under users/{user_id}/...
  |-- Cloudflare Turnstile verifies signup/login tokens server-side
  |-- Mailpit receives staging emails via SMTP (internal only)

MinIO console is exposed directly at http://localhost:9001 for local admin testing only.
```

## Services

- `nginx`: reverse proxy on `http://localhost`
- `frontend`: Next.js App Router UI
- `backend`: FastAPI API under `/api`
- `postgres`: local PostgreSQL, Docker-network only
- `minio`: local private object storage, console on `localhost:9001`
- `minio-init`: one-shot bucket creation with private anonymous policy
- `mailpit`: local SMTP catcher; web UI at `localhost:8025` direct (admin) or `/mailpit/` through Nginx (challenge mode only)

## Setup

```bash
cd hypervaults
cp .env.example .env
docker compose up --build
```

For event-specific flags and challenge credentials, edit `.env` on the workshop host:

```env
FLAG_DOCS_BYPASS=flag{your_docs_flag}
FLAG_TRACE_MAIL=flag{your_trace_flag}
FLAG_MAILPIT_INBOX=flag{your_mailpit_flag}
FLAG_MINIO_PUBLIC_BUCKET=flag{your_minio_flag}
FLAG_HARBOR_DEBUG_IMAGE=flag{your_harbor_flag}
MAILPIT_BASIC_USER=devmail
MAILPIT_BASIC_PASSWORD=change-this-for-your-event
```

Do not put these values in Dockerfiles. Compose passes them into the containers at runtime, which is easier to change on a DigitalOcean droplet without rebuilding images. The values in `.env.example` are fake CTF values only.

If you previously started an older version of this stack and Postgres logs an error about data in `/var/lib/postgresql/data`, recreate the local Postgres volume:

```bash
docker compose down
docker volume rm hypervaults_postgres-data 2>/dev/null || true
docker compose up --build
```

The current Compose file uses the Postgres 18-compatible `postgres-18-data` volume mounted at `/var/lib/postgresql`.

Then open:

- App: http://localhost
- App fallback if your browser prefers a broken IPv6 localhost path: http://127.0.0.1
- MinIO console: http://localhost:9001

## Secure Mode Smoke Test

Use secure mode for the baseline app:

```env
CHALLENGE_MODE=false
NGINX_CONFIG_FILE=./nginx/nginx.conf
ENABLE_X_FORWARDED_DOCS_BYPASS=false
ENABLE_TRACE_MAIL_DIAGNOSTICS=false
ENABLE_MAILPIT_EXPOSURE=false
ENABLE_PUBLIC_MINIO_BUCKET=false
ENABLE_OBJECTS_GATEWAY=false
ENABLE_HARBOR_REGISTRY=false
ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=false
```

Start and verify:

```bash
docker compose up --build --force-recreate
sh scripts/verify_lab.sh
```

Expected secure-mode checks:

```bash
curl -i http://localhost/api/health
curl -i http://localhost/api/docs
curl -i -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/docs
curl -i -X TRACE http://localhost/api/diagnostics/mail
curl -i http://localhost/mailpit/
curl -i http://localhost/objects/hypervaults-files/flag.txt
```

Docs, TRACE diagnostics, Mailpit, and `/objects` should not be publicly reachable.

## Challenge Mode Smoke Test

Use challenge mode only for disposable CTF infrastructure:

```env
CHALLENGE_MODE=true
NGINX_CONFIG_FILE=./nginx/nginx.conf.challenge
ENABLE_X_FORWARDED_DOCS_BYPASS=true
ENABLE_TRACE_MAIL_DIAGNOSTICS=true
ENABLE_MAILPIT_EXPOSURE=true
ENABLE_PUBLIC_MINIO_BUCKET=true
ENABLE_OBJECTS_GATEWAY=true
ENABLE_HARBOR_REGISTRY=true
ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=true
```

Restart and verify:

```bash
docker compose down
docker compose up --build --force-recreate
sh scripts/verify_lab.sh
```

Branch checks:

```bash
# Branch 1: spoofed localhost docs bypass
curl -i http://localhost/api/docs
curl -s -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/openapi.json | grep trusted_proxy_headers

# Branch 2: TRACE mail diagnostics
curl -s -X TRACE -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/diagnostics/mail

# Branch 3: exposed Mailpit
curl -i http://localhost/mailpit/
# open http://localhost/mailpit/ and use the credentials leaked by TRACE

# Branch 4: public MinIO object gateway
curl -s "http://localhost/objects/hypervaults-files/?list-type=2"
curl -s http://localhost/objects/hypervaults-files/flag.txt
```

Harbor is a separate optional stack. See [harbor/README.md](harbor/README.md) before enabling the registry branch.

## Stopping and Resetting

Stop services without deleting state:

```bash
docker compose down
```

Reset database and object storage intentionally:

```bash
docker compose down -v
```

`docker compose down -v` deletes PostgreSQL and MinIO volume state.

The default `.env.example` uses Cloudflare Turnstile official dummy keys that always pass local validation. For real Turnstile credentials, replace both `NEXT_PUBLIC_TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`.

Cloudflare test key reference: https://developers.cloudflare.com/turnstile/troubleshooting/testing/

By default, `.env.example` also selects the secure Nginx config:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf
CHALLENGE_MODE=false
ENABLE_X_FORWARDED_DOCS_BYPASS=false
ENABLE_TRACE_MAIL_DIAGNOSTICS=false
ENABLE_MAILPIT_EXPOSURE=false
```

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
- Swagger, ReDoc, and OpenAPI JSON are disabled by FastAPI defaults and blocked by Nginx in secure mode.
- TRACE is blocked by Nginx in secure mode.
- `/mailpit` returns 404 in secure mode; Mailpit ports are not published to the host.
- File metadata, download, and delete routes filter by `owner_id`.
- Upload filenames are sanitized.
- Upload size, extensions, content types, and simple file signatures are restricted.
- JWT secret comes from the environment.
- Turnstile is verified server-side for signup and login.
- CORS is restricted to local frontend origins.
- MinIO console is not proxied through Nginx.

## First Challenge Branch: X-Forwarded-For Docs Bypass

This optional challenge demonstrates OWASP A02 Security Misconfiguration. It intentionally combines two mistakes:

- Nginx forwards a client-provided `X-Forwarded-For` value on docs routes.
- FastAPI trusts that forwarding header when deciding whether a request is from localhost.

The flag is:

```text
flag{trusted_proxy_headers_are_not_user_input}
```

### Secure Mode Tests

Use the default `.env` values:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf
CHALLENGE_MODE=false
ENABLE_X_FORWARDED_DOCS_BYPASS=false
```

Start or restart:

```bash
docker compose up --build
```

Expected denied:

```bash
curl -i http://localhost/api/docs
```

Expected denied even with spoofed header:

```bash
curl -i -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/docs
```

### Challenge Mode Tests

Set these values in `.env`:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf.challenge
CHALLENGE_MODE=true
ENABLE_X_FORWARDED_DOCS_BYPASS=true
```

Restart:

```bash
docker compose up --build
```

Expected denied without header:

```bash
curl -i http://localhost/api/docs
```

Expected allowed with spoofed header:

```bash
curl -i -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/docs
```

Expected OpenAPI allowed with spoofed header:

```bash
curl -i -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/openapi.json
```

Expected flag visible:

```bash
curl -s -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/openapi.json | grep trusted_proxy_headers
```

### Security Explanation

`X-Forwarded-For` is a forwarding header used by proxies to record the original client IP address. A public client can also send this header unless the edge proxy strips or overwrites it. If an application treats this value as trustworthy, an attacker can claim to be `127.0.0.1` and reach features meant for localhost-only access.

The correct fix is to keep public docs disabled or guarded by real authentication, make reverse proxies overwrite forwarding headers, and configure applications to trust forwarded headers only from known trusted proxies. Application code should not treat arbitrary client-supplied `X-Forwarded-For` values as proof of internal access.

## Second Challenge Branch: TRACE Mail Diagnostics + Exposed Mailpit

This optional challenge demonstrates OWASP A02 Security Misconfiguration via two related mistakes:

- A TRACE endpoint at `/api/diagnostics/mail` leaks internal mail infrastructure details including Mailpit credentials.
- Mailpit, a development SMTP catcher, is exposed through the reverse proxy with intentionally weak Basic Auth credentials — the same ones leaked by the TRACE endpoint.

The two flags are:

```text
flag{trace_mail_diagnostics_exposed}       ← from the TRACE endpoint
flag{dev_mailboxes_do_not_belong_in_prod}  ← from a seeded email in Mailpit
```

### Expected Secure Mode Behavior

In secure mode (default `.env`):

- `GET /api/diagnostics/mail` → 404 (route not registered)
- `TRACE /api/diagnostics/mail` → 405 (blocked by Nginx)
- `GET /mailpit` → 404 (explicit block in Nginx)
- Mailpit web UI ports are not published to the host

### Challenge Mode: Enable All Four Flags

Set these values in `.env`:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf.challenge
CHALLENGE_MODE=true
ENABLE_X_FORWARDED_DOCS_BYPASS=true
ENABLE_TRACE_MAIL_DIAGNOSTICS=true
ENABLE_MAILPIT_EXPOSURE=true
```

Restart:

```bash
docker compose up --build
```

### Challenge Test Commands

**Step 1 — Use the first vulnerability to access docs:**

```bash
curl -i -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/docs
```

Or inspect the OpenAPI schema directly:

```bash
curl -s -H "X-Forwarded-For: 127.0.0.1" http://localhost/api/openapi.json | python3 -m json.tool | grep -A2 diagnostics
```

**Step 2 — Call the TRACE endpoint:**

```bash
curl -s -X TRACE http://localhost/api/diagnostics/mail \
  -H "X-Forwarded-For: 127.0.0.1" | python3 -m json.tool
```

Expected response includes:

```json
{
  "mail_ui_auth": {
    "type": "basic",
    "username": "devmail",
    "password": "devmail2026"
  },
  "flag": "flag{trace_mail_diagnostics_exposed}"
}
```

**Step 3 — Open Mailpit:**

```text
http://localhost/mailpit/
```

Login with: `devmail` / `devmail2026`

**Step 4 — Find the second flag in a seeded email:**

Look for the email with subject `HyperVaults Mail Diagnostic` sent to `support@hypervaults.local`. Its body contains:

```text
flag{dev_mailboxes_do_not_belong_in_prod}
```

A third seeded email (`Staging dev account` to `dev@hypervaults.local`) hints at a future challenge involving dev credential reuse.

### Notes on Seed Emails

Seed emails are sent once per backend process lifetime. If the backend container is restarted, duplicate emails may appear in Mailpit. This is expected and does not affect the challenge flags.

### Nginx Config Files

| File | Purpose |
|------|---------|
| `nginx/nginx.conf` | Secure mode — TRACE blocked, `/mailpit` returns 404 |
| `nginx/nginx.conf.challenge` | Challenge mode — TRACE allowed to backend, `/mailpit/` proxied with Basic Auth |

The htpasswd entry for Mailpit Basic Auth is generated by the nginx `entrypoint` from Compose environment variables.

### Security Explanation

TRACE is an HTTP method originally designed for diagnostic loop-back testing. It echoes the received request back to the client. Most modern applications and proxies block it because it can leak sensitive headers. When a TRACE-like diagnostic endpoint is left enabled in a staging or production environment and the reverse proxy allows the method through, it becomes an information disclosure vector.

Development mail infrastructure (SMTP catchers, local mailers) should never be accessible from the public internet. Exposing Mailpit through a reverse proxy with weak credentials that are themselves leaked by another endpoint demonstrates how multiple small misconfigurations chain into a significant security failure.

## Third Challenge Branch: Public MinIO Object Storage

This optional challenge demonstrates OWASP A02 Security Misconfiguration via object storage misconfiguration:

- The MinIO bucket policy is set to public read+list, making every uploaded user file accessible without credentials.
- The MinIO object API is exposed through the reverse proxy at `/objects/` without authentication.
- A seeded `flag.txt` at the bucket root provides the challenge flag.
- The download API response includes a direct `public_object_url` pointing at the open gateway, making discovery beginner-friendly — players see the URL pattern after uploading any file.

The flag is:

```text
flag{public_buckets_make_private_uploads_public}
```

### Expected Secure Mode Behavior

In secure mode (default `.env`):

- `GET /objects/` → 404 (explicit block in Nginx)
- `GET /objects/hypervaults-files/` → 404
- Uploaded file downloads require JWT authentication and return a short-lived presigned URL
- `public_object_url` is absent from download responses

### Challenge Mode Environment

Set these values in `.env`:

```env
NGINX_CONFIG_FILE=./nginx/nginx.conf.challenge
CHALLENGE_MODE=true
ENABLE_PUBLIC_MINIO_BUCKET=true
ENABLE_OBJECTS_GATEWAY=true
```

Restart (minio-init must re-run to apply the bucket policy and seed files):

```bash
docker compose down
docker compose up --build
```

### Challenge Test Commands

**Step 1 — Sign up and upload a file:**

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"player@example.com","password":"CorrectHorseBatteryStaple!42","turnstile_token":"XXXX.DUMMY.TOKEN.XXXX"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

printf "test content\n" > test.txt
curl -s -X POST http://localhost/api/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt;type=text/plain"
```

**Step 2 — Request a download and observe the public URL:**

```bash
FILE_ID=$(curl -s http://localhost/api/files -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

curl -s http://localhost/api/files/$FILE_ID/download \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

The response includes `public_object_url` pointing at `/objects/hypervaults-files/users/...`.

**Step 3 — Browse the bucket:**

```bash
curl -s "http://localhost/objects/hypervaults-files/?list-type=2" | python3 -m json.tool
```

Or open in a browser:

```text
http://localhost/objects/hypervaults-files/
```

**Step 4 — Retrieve the flag:**

```bash
curl -s http://localhost/objects/hypervaults-files/flag.txt
```

Expected:

```text
flag{public_buckets_make_private_uploads_public}
```

**Step 5 — Find the hint file:**

```bash
curl -s http://localhost/objects/hypervaults-files/support/old-export-note.txt
```

### Notes on minio-init

The `minio-init` container runs once per `docker compose up` session. If you switch `ENABLE_PUBLIC_MINIO_BUCKET` between runs, bring the stack fully down and back up so `minio-init` re-runs and updates the bucket policy:

```bash
docker compose down
docker compose up --build
```

### Security Explanation

Public object storage buckets are one of the most common cloud misconfigurations. An S3-compatible bucket set to public read/list exposes every object stored in it, regardless of how private the application believes those objects to be. The application-level ownership checks in the download API remain intact, but they are bypassed entirely when the bucket itself is publicly accessible through the storage API.

The correct mitigations are: keep buckets private by default, use pre-signed URLs with short TTLs for object access, never expose the storage API directly to the internet, and audit bucket policies regularly.

## Fourth Challenge Branch: Harbor Registry Default Credentials

This optional challenge demonstrates OWASP A02 Security Misconfiguration via container registry mismanagement:

- Harbor is deployed with its default admin password (`Harbor12345`) never rotated.
- A staging debug image (`hypervaults-api:staging-debug`) is left in the production-facing registry.
- The image contains `build-notes.txt` with the challenge flag.
- Players discover the registry through a Bootstrap email seeded into Mailpit.

The flag is:

```text
flag{debug_images_should_not_reach_prod_registries}
```

### Setup

Harbor runs as a separate Docker Compose stack. See [harbor/README.md](harbor/README.md) for full setup instructions, including:

- Downloading the Harbor installer
- Configuring `harbor.yml` with the challenge credentials
- Creating the project and pushing the debug image
- Adding the `/etc/hosts` entry for local subdomain routing

### Enable the Challenge Branch

In `.env`:

```env
CHALLENGE_MODE=true
ENABLE_HARBOR_REGISTRY=true
ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=true
HARBOR_HOST=registry.hypervaults.local
```

Restart the main stack after enabling so the backend seeds the discovery email:

```bash
docker compose up --build
```

### Player Path

**Step 1 — Find the Harbor email in Mailpit (chained from second branch):**

Open http://localhost/mailpit/, log in with `devmail` / `devmail2026`, and look for **Harbor staging registry bootstrap** in `dev@hypervaults.local`.

**Step 2 — Log in to Harbor:**

```text
http://registry.hypervaults.local
Username: admin
Password: Harbor12345
```

**Step 3 — Pull the debug image:**

```bash
docker login registry.hypervaults.local -u admin -p Harbor12345
docker pull registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug
```

**Step 4 — Recover the flag:**

```bash
docker run --rm registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug
```

Expected output:

```text
flag{debug_images_should_not_reach_prod_registries}
```

### Security Explanation

Container registries frequently inherit default credentials from install scripts and are never hardened before connecting to CI/CD pipelines. Debug or staging images often accumulate internal environment variables, secrets, or build notes that should never leave the development environment. Leaving such images in a shared or production-facing registry — even under a separate tag — exposes them to anyone who can authenticate, and default credentials ensure that threshold is nearly zero.

The correct mitigations are: change the registry admin password immediately after installation, use scoped robot accounts instead of the admin account for CI/CD, enforce image signing, regularly audit and remove stale tags, and never store secrets or flags in image layers.

### Nginx Config Note

`nginx/nginx.conf.challenge` includes a second server block for `registry.hypervaults.local` that proxies to Harbor via `host.docker.internal:8090` (Docker Desktop). On Linux, replace with the Docker bridge IP (`172.17.0.1`) or add `--add-host=host.docker.internal:host-gateway` to the nginx service. Secure mode has no Harbor server block.

## Planned Future Vulnerable Branches

These branches are planned for later challenge work and are not implemented here:

1. Resend support-email branch
2. Broken file authorization branch

## Development Notes

The backend uses `create_all` on startup for the first milestone to keep local setup simple. Alembic migrations should be introduced before this project is used beyond local development.
