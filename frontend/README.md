# HyperVaults Frontend

Next.js App Router frontend for the HyperVaults secure vault baseline.

## Pages

- `/`: landing page
- `/signup`: account creation with Turnstile
- `/login`: login with Turnstile
- `/dashboard`: authenticated file upload, list, download, delete, and logout

## Environment

The frontend uses these public variables:

```env
NEXT_PUBLIC_API_BASE_URL=/api
NEXT_PUBLIC_TURNSTILE_SITE_KEY=1x00000000000000000000AA
```

`NEXT_PUBLIC_TURNSTILE_SITE_KEY` is safe to expose because it is the public widget key. The matching secret belongs only in the backend environment as `TURNSTILE_SECRET_KEY`.

## Local Scripts

```bash
npm install
npm run dev
npm run build
npm run lint
```

The Compose stack builds the production standalone Next.js output.

## Auth Token Storage

This baseline stores the JWT in `localStorage` to keep local development simple and avoid tokens in URLs. Backend authorization remains the security boundary: every protected API route validates the bearer token and every file route checks ownership. For a production browser deployment, revisit session storage, refresh strategy, CSP, and XSS hardening.

## Turnstile

Signup and login forms do not submit until a Turnstile token is available. Failed login/signup attempts reset the widget.

For local UI testing without Cloudflare network calls, set:

```env
TURNSTILE_DEV_BYPASS=true
NEXT_PUBLIC_TURNSTILE_SITE_KEY=dev-bypass
```

The backend still requires the matching explicit bypass token and will reject it unless `TURNSTILE_DEV_BYPASS=true`.
