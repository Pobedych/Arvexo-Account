import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
import redis as redis_lib

from app.core.config import settings
from app.core.errors import bad_request, unauthorized
from app.models.user import User

_redis: redis_lib.Redis | None = None


def _get_redis() -> redis_lib.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = redis_lib.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
        except Exception:
            return None
    return _redis

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


# ── OAuth state (stored in Redis under a short random key) ───────────────────
_OAUTH_STATE_KEY_PREFIX = "oauth_state:"


def create_oauth_state(action: str, user_id: str | None = None, extra: dict | None = None) -> str:
    """Store OAuth state in Redis and return a short opaque token."""
    state_id = secrets.token_urlsafe(16)  # 22 chars — well within Telegram's limit
    data = {
        "action": action,
        "user_id": user_id,
        "extra": extra or {},
    }
    r = _get_redis()
    if r is not None:
        r.setex(
            f"{_OAUTH_STATE_KEY_PREFIX}{state_id}",
            _OAUTH_STATE_TTL_MINUTES * 60,
            json.dumps(data),
        )
    else:
        # Redis unavailable — fall back to signed JWT (may be too long for Telegram)
        now = utc_now()
        payload = {
            "type": "oauth_state",
            "nonce": state_id,
            "action": action,
            "user_id": user_id,
            "extra": extra or {},
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=_OAUTH_STATE_TTL_MINUTES)).timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return state_id


def decode_oauth_state(state: str) -> dict:
    """Retrieve OAuth state from Redis; fall back to JWT verification."""
    r = _get_redis()
    if r is not None:
        raw = r.getdel(f"{_OAUTH_STATE_KEY_PREFIX}{state}")
        if raw:
            return json.loads(raw)
    # Try JWT fallback (old-style states or Redis miss)
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise bad_request("INVALID_STATE", "Invalid or expired OAuth state") from exc
    if payload.get("type") != "oauth_state":
        raise bad_request("INVALID_STATE", "Invalid OAuth state type")
    return payload
