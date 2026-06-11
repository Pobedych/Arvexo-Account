# Arvexo Account

Arvexo Account is the shared account and authentication service for Arvexo products.

This first slice implements Priority 1: Docker, FastAPI backend, PostgreSQL schema, Alembic migration, email/password auth, refresh sessions, and basic Next.js UI.

## Local Run

```bash
docker compose up --build
```

## CI/CD

GitHub Actions deployment is configured in `.github/workflows/deploy.yml`.

Setup instructions and required GitHub Secrets are in `docs/GITHUB_DEPLOY.md`.

Open:

```text
http://localhost:8080
```

Direct backend health:

```text
http://localhost:8000/health
```

Nginx backend health:

```text
http://localhost:8080/api/health
```

Direct frontend container port:

```text
http://localhost:3002
```

## Environment

Development defaults live in `.env.example`. In dev, keep `COOKIE_DOMAIN` empty. Do not set `Domain=localhost`.

For production with:

```text
account.arvexo.ru
api.account.arvexo.ru
```

use:

```env
APP_ENV=production
PUBLIC_SITE_URL=https://account.arvexo.ru
PUBLIC_API_URL=https://api.account.arvexo.ru
FRONTEND_URL=https://account.arvexo.ru
COOKIE_DOMAIN=.account.arvexo.ru
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

Use a long random `JWT_SECRET` in production.

## Backend

Implemented endpoints:

```text
GET  /health
GET  /auth/providers
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh
GET  /auth/me
```

Errors use:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

Refresh tokens are stored only as SHA-256 hashes in PostgreSQL. The raw refresh token is sent only through an `httpOnly` cookie. Access tokens are short-lived JWTs returned in JSON and are not stored in `localStorage`.

## Migrations And Seed

The backend container runs:

```bash
alembic upgrade head
```

To seed local development data after the stack is up:

```bash
docker compose exec backend python -m app.scripts.seed
```

Seed creates:

```text
test@arvexo.ru / password12345
oauth client: arvexo-study
```

The seed is explicit and should not be run automatically in production.

## Frontend

Implemented pages:

```text
/login
/register
/account
```

The UI uses existing Arvexo brand assets from the main site:

```text
frontend/public/images/arvexo-mark.png
frontend/public/images/arvexo-wordmark.png
frontend/public/images/arvexo-lockup.png
```

Google, Yandex, and Telegram buttons stay disabled until provider credentials are configured.

## Arvexo Study SSO

The first slice does not change `Arvexo-Study`. The future SSO contract is documented in `docs/STUDY_SSO.md`.

Study must not receive Account access tokens or refresh tokens. After `/sso/exchange`, Study creates its own local session cookie.

## MVP Limits

Not implemented in Priority 1:

```text
public third-party OAuth provider
billing
subscriptions
marketplace
2FA/TOTP
password reset
full sessions management UI
Google/Yandex/Telegram OAuth callbacks
SSO start/exchange endpoints
```

Do not show these as finished capabilities in the UI until their priority slice is implemented.
