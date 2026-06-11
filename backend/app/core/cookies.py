from fastapi import Response

from app.core.config import settings

REFRESH_COOKIE_NAME = "arvexo_account_refresh"
ACCESS_COOKIE_NAME = "arvexo_account_access"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        domain=settings.cookie_domain,
        path="/",
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        httponly=True,
    )
