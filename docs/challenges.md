# Challenge Catalog

## Headers Don't Lie

- Category: Web / Security Misconfiguration
- Difficulty: Easy
- Points: 100
- Flag: `Securinets{headers_dont_lie_they_get_forwarded}`
- Public description: Internal docs were supposed to stay internal. The proxy might be more trusting than it should be.
- Intended vulnerability: Trusting user-controlled `X-Forwarded-For` for localhost-only documentation access.
- Expected exploit path: Request `/api/docs` or `/api/openapi.json` through the public proxy with `X-Forwarded-For: 127.0.0.1`.
- Author notes: The flag is embedded in the OpenAPI description only when challenge mode or the XFF branch is enabled.
- Reset requirements: None.

## Trace It Till You Make It

- Category: Web / HTTP
- Difficulty: Easy-Medium
- Points: 150
- Flag: `Securinets{trace_it_till_you_make_it}`
- Public description: A diagnostics route survived the staging cutover. It was never meant for browsers.
- Intended vulnerability: `TRACE /api/diagnostics/mail` exposes internal mail diagnostics and credentials.
- Expected exploit path: Use the docs bypass to discover the endpoint, then send `TRACE` with the spoofed localhost header.
- Author notes: Nginx scopes TRACE handling to `/api/diagnostics/mail`; this does not enable TRACE broadly.
- Reset requirements: None.

## Who Sent You?

- Category: Cloud / DevOps
- Difficulty: Medium
- Points: 200
- Flag: `Securinets{dev_mailboxes_do_not_belong_in_prod}`
- Public description: Staging email captured more than test signups. Read carefully; the useful message is not the loudest one.
- Intended vulnerability: Development Mailpit UI is exposed through the public edge with weak credentials leaked by diagnostics.
- Expected exploit path: Use leaked Basic Auth credentials from the TRACE response, open `/mailpit/` or `https://mailpit.hypervaults.io/mailpit/`, and read seeded staging messages.
- Author notes: Nginx blocks destructive methods so players can read but not delete shared mail. If raw Mailpit port 8025 is exposed, this safety control is bypassed.
- Reset requirements: Restart the backend to re-send seeded messages, or run `docker compose down -v` followed by `docker compose up -d --build` for a full reset.

## It Worked On Staging

- Category: Cloud / Object Storage
- Difficulty: Medium
- Points: 250
- Flag: `Securinets{public_buckets_make_private_uploads_public}`
- Public description: The vault issues private download links, but one migration shortcut changed the storage boundary.
- Intended vulnerability: Public read/list MinIO bucket plus unauthenticated `/objects/` gateway.
- Expected exploit path: Create an account, upload and download a file, notice `public_object_url`, strip the object key, list `/objects/hypervaults-files/?list-type=2`, then read `/objects/hypervaults-files/flag.txt`.
- Author notes: Nginx limits the object gateway to `GET` and `HEAD`. The intentional flaw is read exposure, not write access.
- Reset requirements: `docker compose down -v` followed by `docker compose up -d --build` recreates the bucket and seeded objects.

## Debug Image

- Category: Container / Registry
- Difficulty: Medium
- Points: 300
- Flag: `Securinets{debug_images_should_not_reach_prod_registries}`
- Public description: A staging registry is still reachable, and one image was pushed with more context than it needed.
- Intended vulnerability: Optional Harbor branch with weak bootstrap admin credentials and a retained debug image.
- Expected exploit path: Discover Harbor credentials in Mailpit, log in to `registry.hypervaults.io`, pull `hypervaults/hypervaults-api:staging-debug`, and read `/app/build-notes.txt`.
- Author notes: Disabled until Harbor is installed and seeded. Treat Harbor as disposable challenge infrastructure.
- Reset requirements: Re-run `harbor/scripts/setup-harbor-project.sh` and `harbor/scripts/push-debug-image.sh`; reset or destroy Harbor data after the event.
