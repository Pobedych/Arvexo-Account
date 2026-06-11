# Arvexo Study SSO Contract

This document describes the future integration path. The first implementation slice does not change `Arvexo-Study`.

## Flow

1. User opens `study.arvexo.ru/login`.
2. Study redirects to:

```text
https://account.arvexo.ru/sso/start?client_id=arvexo-study&redirect_uri=https://study.arvexo.ru/auth/callback&state=<random>
```

3. Arvexo Account authenticates the user.
4. Account redirects back to Study:

```text
https://study.arvexo.ru/auth/callback?code=<one_time_code>&state=<same_random>
```

5. Study backend calls `/sso/exchange` server-to-server.
6. Study creates its own local session cookie for `study.arvexo.ru`.

## Token Boundary

Study must not receive or store Account access tokens or Account refresh tokens. `/sso/exchange` returns only a minimal account profile and `expires_in`.

Study stores:

```text
local_user_id
arvexo_account_id
study_profile
study_stats
study_subscription
study_settings
```

Study should stop storing account-level password hashes, external provider IDs, and refresh sessions after the migration.

## MVP Status

Priority 1 only documents this contract. `/sso/start` and `/sso/exchange` are roadmap items for Priority 3.
