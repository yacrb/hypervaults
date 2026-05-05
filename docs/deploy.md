# Deployment

These steps target a fresh Ubuntu droplet. DNS is handled manually in Cloudflare.
The vulnerable app is served from the main domain. Only supporting services use
subdomains.

## 1. Cloudflare DNS

Create records yourself in Cloudflare:

```text
Type  Name      Value
A     @         159.223.251.136
A     mailpit   159.223.251.136
A     registry  159.223.251.136   optional Harbor branch
CNAME www       hypervaults.io    optional
```

Use DNS-only mode until Caddy has issued certificates. After the certificates are
valid, Cloudflare proxying is fine if SSL/TLS mode is set to Full or Full strict.
Do not rely on wildcard routing unless you also create a wildcard DNS record and
add explicit Caddy routes for the services you want public.
Use `registry.hypervaults.io` as the only public Harbor hostname.

Do not create an extra challenge subdomain for this stack. The app runs at:

```text
https://hypervaults.io
```

Mailpit runs at:

```text
https://mailpit.hypervaults.io/mailpit/
```

## 2. Install Packages

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git jq caddy

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

## 3. Configure the App

```bash
git clone <your-repo-url> hypervaults
cd hypervaults
cp .env.example .env
nano .env
```

Set these values:

```env
DOMAIN=hypervaults.io
APP_HOST=hypervaults.io
MAILPIT_HOST=mailpit.hypervaults.io
REGISTRY_HOST=registry.hypervaults.io

PUBLIC_APP_URL=https://hypervaults.io
PUBLIC_API_URL=https://hypervaults.io/api
OBJECTS_PUBLIC_BASE_URL=https://hypervaults.io/objects
MINIO_PRESIGNED_PUBLIC_BASE_URL=https://hypervaults.io/minio
MAILPIT_UI_PUBLIC_URL=https://mailpit.hypervaults.io/mailpit/
MAILPIT_API_URL=http://mailpit:8025/mailpit/api/v1/messages
MAILPIT_RESEED_INTERVAL_SECONDS=10
CORS_ALLOWED_ORIGINS=https://hypervaults.io

NEXT_PUBLIC_TURNSTILE_SITE_KEY=<Cloudflare Turnstile site key>
TURNSTILE_SECRET_KEY=<Cloudflare Turnstile secret key>
TURNSTILE_DEV_BYPASS=false

HTTP_BIND=127.0.0.1
HTTP_PORT=8080
POSTGRES_PASSWORD=<random value>
DATABASE_URL=postgresql+psycopg://hypervaults:<same random value>@postgres:5432/hypervaults
JWT_SECRET=<random 32+ byte value>
MINIO_ROOT_PASSWORD=<random value>
MAILPIT_BASIC_PASSWORD=<event value>
```

Generate random values:

```bash
openssl rand -base64 32
```

## 4. Reverse Proxy

The Compose Nginx edge listens on `127.0.0.1:8080`. Caddy terminates public TLS,
redirects `www.hypervaults.io` to the apex, and forwards the main domain plus
service subdomains to that local edge.

```bash
sudo cp caddy/Caddyfile.basic /etc/caddy/Caddyfile

sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

## 5. Start and Verify

```bash
docker compose up -d --build
docker compose ps
BASE_URL=https://hypervaults.io sh scripts/verify_lab.sh
```

Useful logs:

```bash
docker compose logs -f nginx backend
docker compose logs --tail=100 minio minio-init mailpit
```

## 6. Optional Harbor Branch

Harbor is not embedded in the main Compose stack. Follow [harbor/README.md](../harbor/README.md), then enable:

```env
ENABLE_HARBOR_REGISTRY=true
ENABLE_HARBOR_DEFAULT_CREDS_BRANCH=true
HARBOR_HOST=registry.hypervaults.io
HARBOR_ADMIN_USER=admin
HARBOR_ADMIN_PASSWORD=<event Harbor password>
```

Restart and seed the debug image:

```bash
docker compose up -d --build
sh harbor/scripts/setup-harbor-project.sh
sh harbor/scripts/push-debug-image.sh
docker compose restart backend
```

## 7. Reset and Backup

Reset the app-managed PostgreSQL and MinIO state:

```bash
docker compose down -v
docker compose up -d --build
BASE_URL=https://hypervaults.io sh scripts/verify_lab.sh
```
