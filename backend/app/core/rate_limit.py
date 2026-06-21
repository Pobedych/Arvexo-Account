import redis as redis_lib
from fastapi import Request
from starlette import status

from app.core.config import settings
from app.core.errors import ApiError

_redis: redis_lib.Redis | None = None


def _get_redis() -> redis_lib.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = redis_lib.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
        except Exception:
            return None
    return _redis


def _check(key: str, max_attempts: int, window_seconds: int) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        current = r.incr(key)
        if current == 1:
            r.expire(key, window_seconds)
        if current > max_attempts:
            raise ApiError(status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMITED", "Слишком много попыток. Попробуйте позже.")
    except ApiError:
        raise
    except Exception:
        pass


def _ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request) -> None:
    _check(f"rl:login:{_ip(request)}", 5, 300)


def rate_limit_register(request: Request) -> None:
    _check(f"rl:register:{_ip(request)}", 5, 600)


def rate_limit_refresh(request: Request) -> None:
    _check(f"rl:refresh:{_ip(request)}", 30, 60)
