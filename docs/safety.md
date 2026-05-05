# HyperVaults Safety Checklist

HyperVaults challenge mode is intentionally vulnerable. Treat every enabled branch as hostile workshop infrastructure.

- Never run challenge mode on infrastructure containing real data.
- Do not reuse real credentials, API tokens, passwords, or flags.
- Do not connect Harbor, Gitea, MinIO, Mailpit, PostgreSQL, or any lab service to production systems.
- Do not expose the Docker socket to player-controlled services.
- Do not expose PostgreSQL, Redis, MinIO console, internal admin panels, or raw service ports to players.
- Keep any scoring platform separate from challenge infrastructure and back it up separately.
- Keep Mailpit as a capture-only development mailbox. Do not configure it to send real email.
- Keep MinIO buckets private in secure mode and verify public policies are removed after object-storage challenges.
- Keep Cloudflare, Nginx, or an equivalent edge proxy in front of any public workshop deployment.
- Rate-limit public endpoints if hosted outside a local classroom network.
- Reset seeded data before each workshop when players need a clean environment.
- Use only fake training values in `.env`; never paste production credentials or unrelated secrets into the lab configuration.
- Destroy or reset lab services after the event.
