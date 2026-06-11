# ТЗ для Codex: Arvexo Account

## 0. Кратко

Нужно реализовать отдельный сервис **Arvexo Account** — единый аккаунт и авторизацию для продуктов Arvexo.

Домены:

```text
account.arvexo.ru      — frontend auth/account UI
api.account.arvexo.ru  — backend API
```

Целевые клиенты:

```text
study.arvexo.ru
arvexo.ru
ai-shop.arvexo.ru
family.arvexo.ru
будущие сервисы Arvexo
```

Главная идея:

```text
Пользователь открывает любой сервис Arvexo
→ нажимает "Войти"
→ попадает на account.arvexo.ru
→ входит через email / Google / Yandex / Telegram
→ возвращается обратно в исходный сервис уже авторизованным
```

Важно: на текущем этапе это **MVP отдельного auth-сервиса**, но его надо проектировать так, чтобы позже без полного переписывания перейти к полноценному OAuth2/OIDC-подобному flow.

Первый implementation slice для Codex ограничен **Priority 1**:

```text
Docker Compose
Backend skeleton
PostgreSQL models + Alembic
Email/password register/login/logout/refresh/me
Sessions backend foundation
Frontend login/register/account
README/.env/nginx
```

Priority 2–4 остаются в ТЗ как roadmap и не должны показываться в UI как уже реализованные возможности.

---

## 1. Главная цель

Сделать отдельный проект `Arvexo-Account`, который отвечает за:

1. регистрацию и вход пользователей;
2. хранение единого профиля пользователя Arvexo;
3. привязку нескольких способов входа к одному пользователю;
4. управление сессиями;
5. безопасную выдачу коротких access token и refresh-сессий;
6. подключение сервисов Arvexo как клиентов;
7. внутренний SSO-flow для сервисов Arvexo;
8. страницу управления аккаунтом;
9. audit log по важным auth-действиям;
10. подготовку к будущему подключению Arvexo Study и других сервисов.

---

## 2. Технологический стек

### Backend

Использовать:

```text
Python 3.12+
FastAPI
PostgreSQL
SQLAlchemy 2.x
Alembic
Redis
Pydantic v2
python-jose или PyJWT
passlib/bcrypt или argon2
httpx
uvicorn/gunicorn
```

### Frontend

Использовать:

```text
Next.js
React
TypeScript
Tailwind CSS
```

Можно использовать App Router.

### DevOps

Использовать:

```text
Docker
Docker Compose
Nginx
.env файлы
```

Проект должен запускаться локально одной командой:

```bash
docker compose up --build
```

---

## 3. Репозиторий

Сделать структуру:

```text
Arvexo-Account/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── cookies.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── auth_identity.py
│   │   │   ├── session.py
│   │   │   ├── oauth_client.py
│   │   │   ├── sso_code.py
│   │   │   └── audit_log.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── token_service.py
│   │   │   ├── oauth_service.py
│   │   │   ├── telegram_service.py
│   │   │   ├── sso_service.py
│   │   │   └── audit_service.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── oauth.py
│   │   │       ├── telegram.py
│   │   │       ├── account.py
│   │   │       ├── sessions.py
│   │   │       ├── sso.py
│   │   │       └── health.py
│   │   └── tests/
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── register/
│   │   ├── account/
│   │   ├── security/
│   │   ├── connected/
│   │   ├── sessions/
│   │   ├── delete-account/
│   │   └── oauth/authorize/
│   ├── components/
│   ├── lib/
│   ├── Dockerfile
│   └── package.json
│
├── nginx/
│   └── default.conf
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Можно немного менять структуру, если есть разумная причина, но нельзя смешивать всю логику в один файл.

---

## 4. Брендинг и продуктовые ограничения

В интерфейсе использовать бренд:

```text
Arvexo Account
```

Логотипы и бренд-активы брать из главного сайта Arvexo:

```text
Arvexo/public/images/arvexo-mark.png
Arvexo/public/images/arvexo-wordmark.png
Arvexo/public/images/arvexo-lockup.png
```

В `Arvexo-Account` нужно скопировать эти файлы в `frontend/public/images/` и использовать их в UI. Не генерировать новый несовместимый знак Arvexo.

Нельзя писать, что уже есть готовые:

```text
платежи
подписки
единый биллинг
полноценный публичный SSO для сторонних разработчиков
маркетплейс приложений
```

если это реально не реализовано.

Разрешённый wording:

```text
Единый аккаунт для сервисов Arvexo.
Войдите, чтобы продолжить в сервис Arvexo.
Управляйте способами входа и активными сессиями.
```

Запрещённый wording:

```text
Оплачивайте все сервисы через Arvexo Account.
Подключите любой внешний сервис.
Полноценный SSO уже доступен всем.
```

---

## 5. Роли пользователей

В таблице `users.role` предусмотреть роли:

```text
user
admin
service
```

На MVP достаточно роли `user`, но структура должна поддерживать остальные.

---

## 6. База данных

Использовать PostgreSQL.

### 6.1. Таблица users

```sql
users
- id: UUID, primary key
- email: varchar, unique, nullable
- password_hash: varchar, nullable
- name: varchar, nullable
- last_name: varchar, nullable
- phone: varchar, nullable
- avatar_url: text, nullable
- role: varchar, default 'user'
- is_active: boolean, default true
- is_banned: boolean, default false
- email_verified_at: timestamp, nullable
- created_at: timestamp
- updated_at: timestamp
- last_login_at: timestamp, nullable
```

Правила:

1. `email` может быть `NULL`, потому что Telegram-аккаунт может не дать email.
2. Если email есть, он должен быть уникальным.
3. Пароль хранить только как hash.
4. `is_banned=true` запрещает вход.
5. Soft delete не обязателен для MVP, но удаление аккаунта должно корректно чистить связанные данные.

### 6.2. Таблица auth_identities

```sql
auth_identities
- id: UUID, primary key
- user_id: UUID, foreign key users.id, cascade delete
- provider: varchar
- provider_user_id: varchar
- provider_email: varchar, nullable
- created_at: timestamp
- updated_at: timestamp
```

Провайдеры:

```text
email
google
yandex
telegram
```

Индексы:

```sql
unique(provider, provider_user_id)
index(user_id)
index(provider_email)
```

Правила:

1. Один внешний аккаунт нельзя привязать к двум пользователям.
2. Если пользователь уже авторизован и подключает Google/Yandex/Telegram, identity привязывается к текущему `user_id`.
3. Если пользователь не авторизован и входит через внешний провайдер:
   - если identity уже есть — войти в существующий аккаунт;
   - если identity нет, но email совпадает с существующим пользователем — не сливать автоматически без безопасной проверки;
   - если identity нет и безопасного совпадения нет — создать нового пользователя.

### 6.3. Таблица sessions

```sql
sessions
- id: UUID, primary key
- user_id: UUID, foreign key users.id, cascade delete
- refresh_token_hash: varchar
- user_agent: text, nullable
- ip_address: varchar, nullable
- expires_at: timestamp
- revoked_at: timestamp, nullable
- created_at: timestamp
- updated_at: timestamp
```

Правила:

1. Refresh token хранить в БД только в виде hash.
2. Сам refresh token отдавать только в `httpOnly` cookie.
3. При logout проставлять `revoked_at`.
4. При удалении аккаунта удалять все sessions.
5. Нужна страница просмотра активных сессий.

### 6.4. Таблица oauth_clients

```sql
oauth_clients
- id: UUID, primary key
- client_id: varchar, unique
- client_secret_hash: varchar
- name: varchar
- allowed_redirect_uris: jsonb
- allowed_origins: jsonb
- is_active: boolean, default true
- created_at: timestamp
- updated_at: timestamp
```

Пример клиента:

```json
{
  "client_id": "arvexo-study",
  "name": "Arvexo Study",
  "allowed_redirect_uris": [
    "https://study.arvexo.ru/auth/callback",
    "http://localhost:3001/auth/callback"
  ],
  "allowed_origins": [
    "https://study.arvexo.ru",
    "http://localhost:3001"
  ]
}
```

### 6.5. Таблица sso_codes

Одноразовые коды для внутреннего SSO.

```sql
sso_codes
- id: UUID, primary key
- code_hash: varchar, unique
- user_id: UUID, foreign key users.id, cascade delete
- client_id: varchar
- redirect_uri: text
- scope: varchar, nullable
- state: varchar, nullable
- expires_at: timestamp
- used_at: timestamp, nullable
- created_at: timestamp
```

Правила:

1. Код живёт 1–5 минут.
2. Код одноразовый.
3. Код хранить только как hash.
4. После обмена проставлять `used_at`.
5. Нельзя обменять код с другим `client_id`.

### 6.6. Таблица audit_logs

```sql
audit_logs
- id: UUID, primary key
- user_id: UUID, nullable
- action: varchar
- provider: varchar, nullable
- ip_address: varchar, nullable
- user_agent: text, nullable
- metadata: jsonb, nullable
- created_at: timestamp
```

Логировать:

```text
register
login_success
login_failed
logout
refresh
connect_provider
disconnect_provider
delete_account
session_revoked
sso_authorize
sso_token_exchange
password_changed
```

---

## 7. Авторизация и токены

### 7.1. Access token

Access token:

```text
JWT
TTL: 10–15 минут
```

Payload:

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "role": "user",
  "type": "access",
  "iat": 1234567890,
  "exp": 1234567890
}
```

Access token можно возвращать в JSON-ответе и/или ставить в cookie для frontend account-сервиса.

Запрещено хранить access token в `localStorage`.

### 7.2. Refresh token

Refresh token:

```text
случайная криптостойкая строка
TTL: 30 дней
хранится в httpOnly cookie
в БД хранится только hash
```

Cookie:

```text
httpOnly=true
secure=true в production
sameSite=lax
path=/auth/refresh или /
domain=account.arvexo.ru
```

В dev-режиме:

1. `secure=false`.
2. `COOKIE_DOMAIN` оставлять пустым или не задавать.
3. Не использовать `Domain=localhost`, потому что браузеры нестабильно обрабатывают cookie domain для localhost.

В production:

1. `secure=true`.
2. Cookie domain должен быть совместим с `account.arvexo.ru` и `api.account.arvexo.ru`.
3. Рекомендуемое значение: `.account.arvexo.ru`.
4. Если frontend и API окажутся на одном host за reverse proxy, допустимо не задавать domain и использовать host-only cookie.

---

## 8. API

Все ответы API должны быть в JSON.

Ошибки возвращать единообразно:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

Не отдавать stack trace пользователю.

---

## 9. Auth API

### POST /auth/register

Регистрация по email/password.

Request:

```json
{
  "email": "alexey@example.com",
  "password": "StrongPassword123",
  "name": "Alexey"
}
```

Response:

```json
{
  "user": {
    "id": "uuid",
    "email": "alexey@example.com",
    "name": "Alexey",
    "role": "user"
  },
  "access_token": "jwt"
}
```

Действия:

1. провалидировать email;
2. проверить уникальность email;
3. проверить сложность пароля;
4. создать `users`;
5. создать `auth_identities` с provider=`email`;
6. создать refresh-сессию;
7. поставить refresh cookie;
8. залогировать `register`.

### POST /auth/login

Request:

```json
{
  "email": "alexey@example.com",
  "password": "StrongPassword123"
}
```

Действия:

1. найти пользователя по email;
2. проверить пароль;
3. проверить `is_active` и `is_banned`;
4. создать новую session;
5. обновить `last_login_at`;
6. поставить refresh cookie;
7. вернуть access token;
8. залогировать успех/ошибку.

### POST /auth/logout

Действия:

1. найти текущую refresh-сессию;
2. пометить её revoked;
3. удалить refresh cookie;
4. залогировать logout.

### POST /auth/refresh

Действия:

1. взять refresh token из cookie;
2. найти hash в `sessions`;
3. проверить `expires_at` и `revoked_at`;
4. выпустить новый access token;
5. опционально сделать rotation refresh token;
6. вернуть access token.

### GET /auth/me

Вернуть текущего пользователя.

Response:

```json
{
  "id": "uuid",
  "email": "alexey@example.com",
  "name": "Alexey",
  "last_name": null,
  "phone": null,
  "avatar_url": null,
  "role": "user",
  "connected_providers": ["email", "google"],
  "created_at": "..."
}
```

### DELETE /auth/me

Удаление аккаунта.

Действия:

1. проверить текущего пользователя;
2. удалить/анонимизировать данные account-сервиса;
3. удалить identities;
4. удалить sessions;
5. удалить sso_codes;
6. залогировать delete_account до удаления или сохранить системный audit без персональных данных;
7. удалить refresh cookie.

---

## 10. Account API

### PATCH /account/profile

Обновление профиля.

Request:

```json
{
  "name": "Alexey",
  "last_name": "Doborin",
  "phone": "+79990000000",
  "avatar_url": "https://..."
}
```

### GET /account/identities

Список подключённых способов входа.

Response:

```json
[
  {
    "provider": "email",
    "provider_email": "alexey@example.com",
    "created_at": "..."
  },
  {
    "provider": "google",
    "provider_email": "alexey@gmail.com",
    "created_at": "..."
  }
]
```

### DELETE /account/identities/{provider}

Отвязка способа входа.

Правила:

1. Нельзя отвязать последний способ входа.
2. Нельзя отвязать provider, которого нет.
3. Логировать `disconnect_provider`.

---

## 11. Sessions API

### GET /sessions

Вернуть список активных сессий пользователя.

Response:

```json
[
  {
    "id": "uuid",
    "user_agent": "...",
    "ip_address": "...",
    "created_at": "...",
    "expires_at": "...",
    "current": true
  }
]
```

### DELETE /sessions/{session_id}

Завершить конкретную сессию.

### DELETE /sessions

Завершить все сессии кроме текущей.

---

## 12. OAuth / внешние провайдеры

Нужно подготовить поддержку:

```text
Google
Yandex
Telegram
```

### 12.1. Google

Endpoints:

```text
GET /auth/google
GET /auth/google/callback
GET /auth/google/connect
GET /auth/google/connect/callback
```

Логика:

1. `/auth/google` начинает вход через Google.
2. `/callback` получает code.
3. Backend меняет code на профиль.
4. По `google.sub` ищет `auth_identities`.
5. Если найдено — логинит пользователя.
6. Если не найдено — создаёт пользователя или запускает безопасную привязку.
7. `/connect` доступен только авторизованному пользователю и привязывает Google к текущему `user_id`.

### 12.2. Yandex

Endpoints:

```text
GET /auth/yandex
GET /auth/yandex/callback
GET /auth/yandex/connect
GET /auth/yandex/connect/callback
```

Логика аналогична Google.

### 12.3. Telegram

Endpoints:

```text
POST /auth/telegram
POST /auth/telegram/connect
```

Проверять подпись Telegram Login Widget по официальному алгоритму.

Request:

```json
{
  "id": 789012345,
  "first_name": "Alexey",
  "last_name": "Doborin",
  "username": "alexey",
  "photo_url": "https://...",
  "auth_date": 1234567890,
  "hash": "..."
}
```

Правила:

1. Проверить hash.
2. Проверить, что `auth_date` не слишком старый.
3. `provider_user_id = telegram_id`.
4. При `/connect` привязать к текущему пользователю.
5. Нельзя привязать один Telegram к двум пользователям.

---

## 13. Внутренний SSO для сервисов Arvexo

На MVP реализовать упрощённый SSO, похожий на Authorization Code flow.

### 13.1. GET /sso/start

Request:

```text
GET /sso/start?client_id=arvexo-study&redirect_uri=https://study.arvexo.ru/auth/callback&state=random
```

Логика:

1. Проверить `client_id`.
2. Проверить, что `redirect_uri` входит в `allowed_redirect_uris`.
3. Если пользователь не авторизован в Arvexo Account:
   - сохранить параметры flow;
   - отправить на страницу login.
4. Если пользователь авторизован:
   - создать одноразовый `code`;
   - сохранить `code_hash` в `sso_codes`;
   - redirect на:

```text
https://study.arvexo.ru/auth/callback?code=...&state=random
```

### 13.2. POST /sso/exchange

Request:

```json
{
  "client_id": "arvexo-study",
  "client_secret": "plain_secret",
  "code": "one_time_code",
  "redirect_uri": "https://study.arvexo.ru/auth/callback"
}
```

Response:

```json
{
  "account_user": {
    "id": "uuid",
    "email": "alexey@example.com",
    "name": "Alexey",
    "avatar_url": null
  },
  "expires_in": 900
}
```

Правила:

1. Проверить client secret.
2. Проверить code hash.
3. Проверить `expires_at`.
4. Проверить `used_at is null`.
5. Проверить совпадение `client_id` и `redirect_uri`.
6. Пометить code использованным.
7. Вернуть минимальные данные пользователя.
8. Не отдавать лишние персональные данные без scope.

### 13.3. Важное ограничение

В MVP не нужно делать публичный OAuth provider для сторонних сервисов. Нужно сделать внутренний SSO только для сервисов Arvexo.

---

## 14. Frontend

Нужно сделать аккуратный минималистичный интерфейс в стиле Arvexo.

Стиль:

```text
тёмная тема
технологичный вид
акцент на AI / security / ecosystem
без перегруза
адаптивно под mobile/desktop
```

### 14.1. Страницы

#### /login

Элементы:

1. логотип/название `Arvexo Account`;
2. заголовок: `Войдите в Arvexo Account`;
3. email/password форма;
4. кнопки:
   - `Войти через Google`;
   - `Войти через Яндекс`;
   - `Войти через Telegram`;
5. ссылка на регистрацию;
6. текст: `Единый аккаунт для сервисов Arvexo`.

#### /register

Элементы:

1. email;
2. password;
3. name;
4. кнопка регистрации;
5. ссылка на вход;
6. кнопки внешних провайдеров.

#### /account

Показывает:

1. email;
2. имя;
3. аватар;
4. дату создания;
5. подключённые провайдеры;
6. быстрые ссылки:
   - безопасность;
   - активные сессии;
   - удалить аккаунт.

#### /security

Показывает:

1. смену пароля;
2. подключённые способы входа;
3. кнопки `Подключить Google/Yandex/Telegram`;
4. кнопки отвязки.

#### /sessions

Показывает активные сессии:

```text
Устройство / браузер
IP
Дата входа
Истекает
Текущая сессия или нет
```

Кнопки:

```text
Завершить эту сессию
Завершить все остальные
```

#### /delete-account

Страница удаления аккаунта.

Требования:

1. предупреждение;
2. повторный ввод email;
3. кнопка удаления;
4. подтверждение перед отправкой.

#### /oauth/authorize или /sso/continue

Страница, которая появляется при входе из другого сервиса.

Показывает:

```text
Вы входите в Arvexo Study через Arvexo Account.
```

Кнопки:

```text
Продолжить
Сменить аккаунт
```

---

## 15. Интеграция с Arvexo Study

Подготовить документацию, как Study должен подключаться.

### 15.1. До выноса отдельного сервиса

Если текущая авторизация пока остаётся внутри Study, UI должен использовать wording:

```text
Arvexo Account
```

Но не должен создавать иллюзию, что уже есть отдельный публичный auth-сервис, если он ещё не подключён.

### 15.2. После подключения Account

Study больше не хранит:

```text
password_hash
google_sub
yandex_id
telegram_id
refresh sessions account-уровня
```

Study хранит только:

```text
local_user_id
arvexo_account_id
study_profile
study_stats
study_subscription
study_settings
```

Flow:

```text
study.arvexo.ru/login
→ account.arvexo.ru/sso/start?client_id=arvexo-study&redirect_uri=...
→ login/register на account.arvexo.ru
→ callback в Study
→ Study вызывает /sso/exchange
→ Study создаёт локальную session cookie
```

Важно:

1. Study не получает access token или refresh token Account-сервиса.
2. Account после `/sso/exchange` отдаёт только минимальный профиль пользователя и срок действия результата.
3. Study создаёт собственную локальную session cookie для `study.arvexo.ru`.
4. Study не должен хранить account-level refresh sessions.

---

## 16. ENV

Создать `.env.example`.

```env
APP_ENV=development

# Backend
API_HOST=0.0.0.0
API_PORT=8000
PUBLIC_SITE_URL=http://localhost:3000
PUBLIC_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql+psycopg://arvexo:arvexo@postgres:5432/arvexo_account

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET=change_me
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=30

# Cookies
COOKIE_DOMAIN=
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_REDIRECT_URI=http://localhost:8000/auth/yandex/callback

TELEGRAM_BOT_TOKEN=

# Initial client
SEED_ARVEXO_STUDY_CLIENT=true
ARVEXO_STUDY_CLIENT_ID=arvexo-study
ARVEXO_STUDY_CLIENT_SECRET=dev_secret
ARVEXO_STUDY_REDIRECT_URI=http://localhost:3001/auth/callback
```

Для production:

```env
APP_ENV=production
PUBLIC_SITE_URL=https://account.arvexo.ru
PUBLIC_API_URL=https://api.account.arvexo.ru
FRONTEND_URL=https://account.arvexo.ru
COOKIE_DOMAIN=account.arvexo.ru
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

Если backend доступен на `api.account.arvexo.ru`, а frontend на `account.arvexo.ru`, production `COOKIE_DOMAIN` рекомендуется поставить `.account.arvexo.ru`.

---

## 17. Docker Compose

`docker-compose.yml` должен поднимать:

```text
postgres
redis
backend
frontend
nginx
```

Требования:

1. Postgres с volume.
2. Redis с volume или без, для MVP можно без.
3. Backend зависит от Postgres и Redis.
4. Frontend зависит от backend.
5. Nginx проксирует:
   - `/api/*` на backend;
   - остальное на frontend.
6. Добавить healthcheck для backend.

---

## 18. Nginx

Локально можно:

```text
http://localhost
```

Production-концепция:

```text
account.arvexo.ru      -> frontend
api.account.arvexo.ru  -> backend
```

Nginx должен поддерживать proxy headers:

```text
X-Forwarded-For
X-Forwarded-Proto
Host
```

---

## 19. Безопасность

Обязательно:

1. Refresh token только в `httpOnly` cookie.
2. Не хранить access token в `localStorage`.
3. `secure=true` для cookies в production.
4. `sameSite=lax` или строже.
5. Rate limit на:
   - login;
   - register;
   - refresh;
   - OAuth callback;
   - Telegram login;
   - password reset, если реализован.
6. Password hash через bcrypt/argon2.
7. Уникальность внешних identity.
8. Защита от CSRF там, где используются cookie-based действия.
9. Проверять `redirect_uri` только по allowlist.
10. Не принимать произвольный `return_to` без проверки.
11. Не отдавать чужие данные между сервисами без scope.
12. Не логировать plain password, access token, refresh token, OAuth code.
13. Audit log для важных действий.
14. CORS только для разрешённых origins.
15. В production отключить debug tracebacks.
16. Нельзя использовать wildcard `*` для CORS в production.
17. При удалении аккаунта чистить identities, sessions и временные SSO-коды.
18. Нельзя отвязать последний способ входа.

---

## 20. Rate limit

Можно реализовать через Redis.

Примерные лимиты:

```text
POST /auth/login: 5 попыток / 5 минут на IP + email
POST /auth/register: 5 попыток / 10 минут на IP
POST /auth/telegram: 10 попыток / 5 минут на IP
POST /auth/refresh: 30 попыток / минуту на IP
OAuth callback: 20 попыток / 5 минут на IP
```

При превышении:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many attempts. Try again later."
  }
}
```

---

## 21. Миграции и seed

Сделать Alembic migrations.

Нужен seed для dev:

1. создать test user:
   - email: `test@arvexo.ru`
   - password: `password12345`
2. создать oauth client:
   - client_id: `arvexo-study`
   - redirect_uri: `http://localhost:3001/auth/callback`

Seed не должен запускаться автоматически в production без явного флага.

---

## 22. Тесты

Добавить backend-тесты.

Минимум покрыть:

1. регистрация;
2. вход;
3. неверный пароль;
4. refresh;
5. logout;
6. получение `/auth/me`;
7. запрет входа banned user;
8. привязка identity;
9. запрет дублирования identity;
10. запрет отвязки последнего identity;
11. создание SSO code;
12. обмен SSO code;
13. запрет повторного использования SSO code;
14. запрет чужого `redirect_uri`;
15. удаление аккаунта.

Использовать pytest.

---

## 23. README

В README описать:

1. что такое Arvexo Account;
2. как запустить локально;
3. какие env нужны;
4. как применить миграции;
5. как создать dev user/client;
6. как работает SSO-flow;
7. как подключить новый сервис Arvexo;
8. какие endpoints есть;
9. какие ограничения у MVP.

---

## 24. Критерии готовности

Проект считается готовым, если:

1. `docker compose up --build` запускает весь стек.
2. Frontend открывается локально.
3. Backend отдаёт `/health`.
4. Можно зарегистрироваться через email/password.
5. Можно войти через email/password.
6. Refresh cookie ставится как `httpOnly`.
7. `/auth/me` возвращает пользователя.
8. Можно выйти из аккаунта.
9. Можно посмотреть активные сессии.
10. Можно завершить сессию.
11. Можно посмотреть подключённые identities.
12. Нельзя отвязать последний способ входа.
13. Есть заготовки/рабочие endpoints под Google/Yandex/Telegram.
14. Есть SSO-flow для `arvexo-study`.
15. `redirect_uri` проверяется по allowlist.
16. Есть Alembic migrations.
17. Есть `.env.example`.
18. Есть README.
19. Есть базовые tests.
20. В UI нет ложных обещаний про платежи, подписки и публичный SSO.

---

## 25. Что НЕ делать в MVP

Не нужно делать:

1. полноценный публичный OAuth provider для сторонних разработчиков;
2. billing;
3. подписки;
4. магазин приложений;
5. сложную админ-панель;
6. 2FA/TOTP, если это сильно затянет MVP;
7. magic links, если нет SMTP;
8. биометрию;
9. интеграцию со всеми будущими сервисами сразу;
10. хранение OAuth access token внешних провайдеров без необходимости.

---

## 26. Важные UX-тексты

Использовать:

```text
Arvexo Account
Единый аккаунт для сервисов Arvexo
Войдите, чтобы продолжить
Продолжить в Arvexo Study
Подключённые способы входа
Активные сессии
Удалить аккаунт
```

Для ошибок:

```text
Неверный email или пароль.
Этот способ входа уже привязан к другому аккаунту.
Нельзя отвязать последний способ входа.
Сессия истекла. Войдите снова.
Слишком много попыток. Попробуйте позже.
```

---

## 27. Дополнительные требования к Codex

При разработке:

1. Не хардкодить секреты.
2. Не оставлять TODO вместо критичной auth-логики.
3. Не использовать SQLite в итоговом Docker Compose.
4. Не использовать localStorage для токенов.
5. Не делать небезопасный `return_to` redirect.
6. Не смешивать account-профиль и данные конкретных сервисов.
7. Писать код так, чтобы потом можно было подключить Arvexo Study без переписывания всего backend.
8. Все важные решения фиксировать в README.
9. Если OAuth credentials отсутствуют, сделать graceful fallback: кнопки можно скрывать или показывать disabled-состояние.
10. У всех protected endpoints должна быть проверка текущего пользователя.

---

## 28. Приоритет выполнения

### Priority 1 — основа

1. Docker Compose.
2. Backend skeleton.
3. PostgreSQL models.
4. Alembic migrations.
5. Email/password register/login/logout/refresh/me.
6. Sessions.
7. Frontend login/register/account.

### Priority 2 — безопасность и account management

1. Connected identities API.
2. Delete account.
3. Rate limit.
4. Audit log.
5. Session management UI.
6. Security page.

### Priority 3 — SSO

1. `oauth_clients`.
2. `sso_codes`.
3. `/sso/start`.
4. `/sso/exchange`.
5. Документация подключения Arvexo Study.

### Priority 4 — OAuth providers

1. Google.
2. Yandex.
3. Telegram.
4. Connect-flow для каждого провайдера.

---

## 29. Ожидаемый результат

На выходе должен быть рабочий репозиторий `Arvexo-Account`, который можно:

1. запустить локально;
2. развернуть на VPS;
3. подключить к доменам `account.arvexo.ru` и `api.account.arvexo.ru`;
4. использовать как основу для единого аккаунта Arvexo;
5. в будущем подключить к `study.arvexo.ru`, `arvexo.ru`, `ai-shop.arvexo.ru`, `family.arvexo.ru`.
