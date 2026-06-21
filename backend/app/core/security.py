import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import bad_request, unauthorized
from app.models.user import User

ALGORITHM = "HS256"
_OAUTH_STATE_TTL_MINUTES = 10


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user: User) -> str:
    now = utc_now()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise unauthorized("Invalid access token") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise unauthorized("Invalid access token")
    return payload


def user_id_from_token(token: str) -> UUID:
    payload = decode_access_token(token)
    try:
        return UUID(str(payload["sub"]))
    except ValueError as exc:
        raise unauthorized("Invalid access token") from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── OAuth state JWT (used as CSRF protection in OAuth flows) ─────────────────

def create_oauth_state(action: str, user_id: str | None = None, extra: dict | None = None) -> str:
    now = utc_now()
    payload = {
        "type": "oauth_state",
        "nonce": secrets.token_urlsafe(16),
        "action": action,
        "user_id": user_id,
        "extra": extra or {},
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_OAUTH_STATE_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_oauth_state(state: str) -> dict:
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise bad_request("INVALID_STATE", "Invalid or expired OAuth state") from exc
    if payload.get("type") != "oauth_state":
        raise bad_request("INVALID_STATE", "Invalid OAuth state type")
    return payload
