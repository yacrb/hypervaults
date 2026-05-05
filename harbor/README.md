# Harbor Challenge Setup

This directory contains the challenge materials for the fourth HyperVaults vulnerability branch:
**Harbor registry default credentials + exposed staging debug image**.

Harbor is not embedded in the main `docker-compose.yml` because its installer generates its
own multi-service compose stack. Set up Harbor separately, then configure the main stack
with `ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=true` to seed the discovery email into Mailpit.

---

## Prerequisites

- Docker Engine and Docker Compose v2
- `curl` (for the setup script)
- Port **8090** free on your host

---

## 1 — Download and Install Harbor

Download the Harbor **online** installer from the GitHub releases page.
Replace `v2.12.0` with the latest stable version:

```bash
wget https://github.com/goharbor/harbor/releases/download/v2.12.0/harbor-online-installer-v2.12.0.tgz
tar xzvf harbor-online-installer-v2.12.0.tgz
cd harbor
```

---

## 2 — Configure harbor.yml

Copy the template and edit it:

```bash
cp harbor.yml.tmpl harbor.yml
```

Set the following values (HTTP only, no HTTPS needed for local workshop use):

```yaml
hostname: registry.hypervaults.local

http:
  port: 8090

# Comment out or remove the https block entirely:
# https:
#   port: 443
#   certificate: ...
#   private_key: ...

harbor_admin_password: Harbor12345
```

> **Challenge note:** `Harbor12345` is the intentionally default/weak admin password
> for this challenge. Never use it in real environments.

---

## 3 — Install and Start Harbor

```bash
sudo ./install.sh
```

Harbor starts automatically. Verify it is up:

```bash
curl -s http://localhost:8090/api/v2.0/systeminfo | python3 -m json.tool
```

Harbor web UI: http://localhost:8090  
Login: `admin` / `Harbor12345`

---

## 4 — Add hosts Entry (for Nginx subdomain routing)

To use the challenge nginx config's `registry.hypervaults.local` server block:

```bash
# Linux / Mac
echo "127.0.0.1 registry.hypervaults.local" | sudo tee -a /etc/hosts

# Windows (run as Administrator)
# Add this line to C:\Windows\System32\drivers\etc\hosts:
# 127.0.0.1 registry.hypervaults.local
```

After this, Harbor is reachable at `http://registry.hypervaults.local`
(proxied through the main nginx on port 80) in addition to `http://localhost:8090`.

---

## 5 — Create the Project and Push the Debug Image

```bash
# Create 'hypervaults' project in Harbor
sh harbor/scripts/setup-harbor-project.sh

# Build and push the staging-debug image
sh harbor/scripts/push-debug-image.sh
```

Both scripts use `localhost:8090` / `admin` / `Harbor12345` by default.
Override with environment variables if needed:

```bash
HARBOR_HOST=registry.hypervaults.local HARBOR_PORT=80 \
  sh harbor/scripts/push-debug-image.sh
```

---

## 6 — Enable the Challenge Branch in the Main Stack

In `.env`:

```env
CHALLENGE_MODE=true
ENABLE_HARBOR_REGISTRY=true
ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=true
HARBOR_HOST=registry.hypervaults.local
```

Restart the main stack so the backend seeds the discovery email into Mailpit:

```bash
docker compose up --build
```

Open Mailpit at http://localhost/mailpit/ (credentials: `devmail` / `devmail2026`)
and look for the email **Harbor staging registry bootstrap** sent to `dev@hypervaults.local`.

---

## Challenge Walkthrough

### Discovery
Players discover the Harbor email in Mailpit (chained from the TRACE diagnostics branch).
The email reveals:
- The registry URL: `http://registry.hypervaults.local`
- Bootstrap credentials: `admin / Harbor12345`
- An image name: `registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug`

### Login to Harbor UI
```
http://registry.hypervaults.local
Username: admin
Password: Harbor12345
```

### Pull the Image

```bash
docker login registry.hypervaults.local -u admin -p Harbor12345
docker pull registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug
```

Or using the direct port:
```bash
docker login localhost:8090 -u admin -p Harbor12345
docker pull localhost:8090/hypervaults/hypervaults-api:staging-debug
```

### Recover the Flag

```bash
docker run --rm registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug
```

Or explicitly:

```bash
docker run --rm --entrypoint cat \
  registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug \
  /app/build-notes.txt
```

**Expected flag:**

```text
flag{debug_images_should_not_reach_prod_registries}
```

### Bonus — Read the Staging Env File

```bash
docker run --rm --entrypoint cat \
  registry.hypervaults.local/hypervaults/hypervaults-api:staging-debug \
  /app/.env.staging
```

---

## Stopping Harbor

```bash
cd harbor
docker compose down
```

To fully clean up data:

```bash
docker compose down -v
```

---

## Nginx Config Note

The challenge nginx config (`nginx/nginx.conf.challenge`) includes a second server block
for `registry.hypervaults.local` that proxies to Harbor via `host.docker.internal:8090`.

- **Docker Desktop (Mac/Windows):** works out of the box.
- **Linux:** replace `host.docker.internal` with the Docker bridge IP (`172.17.0.1`) or
  add `--add-host=host.docker.internal:host-gateway` to the nginx service in docker-compose.yml.

In secure mode (`nginx/nginx.conf`), there is no Harbor server block — the registry is
completely unreachable through nginx.

---

## File Layout

```
harbor/
  README.md                      ← this file
  challenge-image/
    Dockerfile                   ← builds the staging-debug image
    build-notes.txt              ← contains the flag
    .env.staging                 ← staging config hints
  scripts/
    setup-harbor-project.sh      ← creates the 'hypervaults' project via Harbor API
    push-debug-image.sh          ← builds and pushes the debug image
```
