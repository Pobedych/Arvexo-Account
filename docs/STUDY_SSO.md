# Подключение Arvexo Study к Arvexo Account SSO

## Концепция

Arvexo Account — единый auth-сервис для продуктов Arvexo.
После интеграции Study не хранит пароли, OAuth-идентификаторы и refresh-сессии уровня аккаунта.
Study хранит только свой локальный профиль, привязанный к `arvexo_account_id`.

## Что Study хранит после интеграции

```
study_users
  - id                  (local UUID)
  - arvexo_account_id   (UUID from Account)
  - study_profile
  - study_stats
  - study_subscription
  - study_settings
  - created_at
```

Удаляются из Study: `password_hash`, `google_sub`, `yandex_id`, `telegram_id`, `refresh_sessions`.

## SSO Flow

```
1. Пользователь нажимает "Войти" на study.arvexo.ru
   └─► GET /api/sso/start
         ?client_id=arvexo-study
         &redirect_uri=https://study.arvexo.ru/auth/callback
         &state=<random>

2. Если не авторизован → Account показывает форму входа/регистрации
   Если авторизован  → Account показывает страницу подтверждения (/sso/continue)

3. Пользователь подтверждает → создаётся одноразовый code (TTL 5 мин)
   └─► Redirect: https://study.arvexo.ru/auth/callback?code=...&state=<random>

4. Study-backend обменивает code на профиль пользователя:
   POST /api/sso/exchange
   {
     "client_id":     "arvexo-study",
     "client_secret": "<secret>",
     "code":          "<one_time_code>",
     "redirect_uri":  "https://study.arvexo.ru/auth/callback"
   }

   Response:
   {
     "account_user": { "id": "uuid", "email": "...", "name": "...", "avatar_url": null },
     "expires_in": 300
   }

5. Study: upsert study_users WHERE arvexo_account_id = account_user.id
6. Study создаёт собственную локальную session cookie для study.arvexo.ru
```

## Регистрация клиента (Dev)

В `.env` Arvexo Account предустановлен dev-клиент:

```env
SEED_ARVEXO_STUDY_CLIENT=true
ARVEXO_STUDY_CLIENT_ID=arvexo-study
ARVEXO_STUDY_CLIENT_SECRET=dev_secret
ARVEXO_STUDY_REDIRECT_URI=http://localhost:3001/auth/callback
```

Для production:
1. Добавить запись в `oauth_clients` с production `redirect_uri`.
2. Сгенерировать случайный `client_secret` → сохранить в секретах Study.
3. Установить `ARVEXO_STUDY_CLIENT_SECRET=<production_secret>` в `.env` Account.

## Пример callback-обработчика на стороне Study (Python)

```python
import httpx, secrets

ACCOUNT_API = "https://api.account.arvexo.ru"
CLIENT_ID   = "arvexo-study"
CLIENT_SECRET = "..."       # из секретов
REDIRECT_URI  = "https://study.arvexo.ru/auth/callback"

def start_login(request):
    state = secrets.token_urlsafe(16)
    request.session["sso_state"] = state
    return redirect(
        f"{ACCOUNT_API}/sso/start"
        f"?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={state}"
    )

def auth_callback(request):
    code  = request.query_params["code"]
    state = request.query_params.get("state")
    if state != request.session.pop("sso_state", None):
        raise BadRequest("Invalid state")

    resp = httpx.post(f"{ACCOUNT_API}/sso/exchange", json={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "code": code,           "redirect_uri": REDIRECT_URI,
    })
    resp.raise_for_status()
    account_user = resp.json()["account_user"]

    user = db.query(StudyUser).filter_by(arvexo_account_id=account_user["id"]).first()
    if not user:
        user = StudyUser(arvexo_account_id=account_user["id"], name=account_user["name"])
        db.add(user); db.commit()

    request.session["user_id"] = str(user.id)
    return redirect("/dashboard")
```

## Важные ограничения

- Study **не получает** access token или refresh token Arvexo Account.
- `code` одноразовый, TTL 5 минут. Нельзя использовать повторно.
- `state` обязателен — защита от CSRF.
- `redirect_uri` при обмене должен **точно совпадать** с тем, что в `/sso/start`.
- `client_secret` передаётся только server-to-server, никогда во frontend.

## Эндпоинты SSO

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/sso/start` | Начало SSO flow; редирект к Account/login |
| `GET` | `/sso/client` | Публичная информация о клиенте (имя) |
| `POST` | `/sso/confirm` | Подтверждение пользователем (frontend → Account) |
| `POST` | `/sso/exchange` | Обмен кода на профиль (Study backend → Account) |
