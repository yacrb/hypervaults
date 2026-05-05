# HyperVaults

HyperVaults is a workshop-ready vulnerable application for the Securinets TEK-UP session on modern security misconfigurations. It presents a realistic document-vault product with intentionally vulnerable challenge branches around proxy headers, HTTP diagnostics, exposed development mail, object storage policy, and an optional registry artifact leak.

The vulnerable paths are documented and gated by environment flags. PostgreSQL, MinIO, SMTP, and app internals stay on Docker-internal networks; the only host-facing service is the Nginx edge container.

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
BASE_URL=http://localhost:8080 sh scripts/verify_lab.sh
```

Open:

- App: http://localhost:8080
- Mailpit challenge UI: http://localhost:8080/mailpit/
- MinIO admin console: http://localhost:9001, bound to localhost only

For a public DigitalOcean droplet with DNS and TLS, use [docs/deploy.md](docs/deploy.md).
The ignored local `.env` is set for `hypervaults.io`; `.env.example` keeps safe
placeholder Turnstile values so real secrets are not stored in git.

Hosted URLs for the reserved IP setup:

- App: https://hypervaults.io
- Mailpit challenge UI: https://mailpit.hypervaults.io/mailpit/
- Optional Harbor branch: https://registry.hypervaults.io

## Workshop Defaults

The default `.env.example` enables the main challenge chain:

- `Headers Don't Lie`: spoofed `X-Forwarded-For` access to internal API docs.
- `Trace It Till You Make It`: `TRACE /api/diagnostics/mail` leaks Mailpit access.
- `Who Sent You?`: read-only exposed Mailpit contains seeded staging emails.
- `It Worked On Staging`: public MinIO bucket and object gateway expose staged files.

The Harbor registry branch is documented and ready, but disabled by default because upstream Harbor is installed as its own Compose stack. Enable it after following [harbor/README.md](harbor/README.md).

## Operator Docs

- [docs/deploy.md](docs/deploy.md): DigitalOcean launch, DNS, TLS, logs, backup, reset.
- [docs/architecture.md](docs/architecture.md): network boundaries, exposed routes, safety model.
- [docs/challenges.md](docs/challenges.md): public challenge entries and organizer metadata.
- [docs/solutions.md](docs/solutions.md): intended exploit paths and flags.
- [docs/safety.md](docs/safety.md): event safety checklist.

Reverse proxy helper:

- `caddy/Caddyfile.basic`: app root plus service subdomains. You manage DNS in Cloudflare.

## Common Commands

```bash
docker compose ps
docker compose logs -f nginx backend
BASE_URL=http://localhost:8080 sh scripts/verify_lab.sh
docker compose down -v
docker compose up -d --build
docker compose down
```

`docker compose down -v` deletes the Compose-managed PostgreSQL and MinIO volumes. Use it only as an organizer action.
