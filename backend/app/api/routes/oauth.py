"""
Yandex OAuth routes.
Google is intentionally disabled (no credentials configured).
"""

from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.cookies import REFRESH_COOKIE_NAME, set_refresh_cookie
from app.core.errors import bad_request
from app.core.security import create_oauth_state, decode_oauth_state
from app.db.session import get_db
from app.services.oauth_service import connect_oauth_identity, exchange_yandex_code, upsert_oauth_user
from app.services.session_service import (
    create_refresh_session,
    get_valid_refresh_session,
    request_ip,
    request_user_agent,
)

router = APIRouter(prefix="/auth", tags=["oauth"])

YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"

_FE = lambda path: f"{settings.frontend_url.rstrip('/')}{path}"  # noqa: E731


def _yandex_login_url(redirect_uri: str, state: str) -> str:
    return YANDEX_AUTH_URL + "?" + urlencode({
        "response_type": "code",
        "client_id": settings.yandex_client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "force_confirm": "no",
    })


# ── Yandex login flow ────────────────────────────────────────────────────────

@router.get("/yandex")
def yandex_login() -> RedirectResponse:
    if not settings.oauth_enabled["yandex"]:
        raise bad_request("PROVIDER_DISABLED", "Yandex OAuth is not configured")
    state = create_oauth_state("login")
    return RedirectResponse(_yandex_login_url(settings.yandex_redirect_uri, state), status_code=302)


@router.get("/yandex/callback")
def yandex_callback(
    code: str,
    state: str,
    request: Request,
    response_redirect: RedirectResponse = None,
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    try:
        state_data = decode_oauth_state(state)
        if state_data.get("action") != "login":
            raise bad_request("INVALID_STATE", "Invalid state action")

        profile = exchange_yandex_code(
            settings.yandex_client_id,
            settings.yandex_client_secret,
            code,
            settings.yandex_redirect_uri,
        )
        user, _ = upsert_oauth_user(
            db, "yandex", profile,
            request_ip=request_ip(request),
            request_ua=request_user_agent(request),
        )
        refresh_token, _ = create_refresh_session(db, user, request)
        db.commit()

        redirect = RedirectResponse(_FE("/oauth/callback"), status_code=302)
        set_refresh_cookie(redirect, refresh_token)
        return redirect
    except Exception as exc:
        from urllib.parse import quote
        msg = exc.detail["message"] if hasattr(exc, "detail") and isinstance(exc.detail, dict) else str(exc)
        return RedirectResponse(_FE(f"/login?error={quote(msg)}"), status_code=302)


# ── Yandex connect flow ──────────────────────────────────────────────────────

@router.get("/yandex/connect")
def yandex_connect(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    if not settings.oauth_enabled["yandex"]:
        raise bad_request("PROVIDER_DISABLED", "Yandex OAuth is not configured")

    session = get_valid_refresh_session(db, refresh_token) if refresh_token else None
    if not session or not session.user:
        return RedirectResponse(_FE("/login"), status_code=302)

    user_id = str(session.user.id)
    state = create_oauth_state("connect", user_id=user_id)
    connect_redirect_uri = settings.yandex_redirect_uri.replace("/callback", "/connect/callback")
    return RedirectResponse(_yandex_login_url(connect_redirect_uri, state), status_code=302)


@router.get("/yandex/connect/callback")
def yandex_connect_callback(
    code: str,
    state: str,
    request: Request,
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    try:
        state_data = decode_oauth_state(state)
        if state_data.get("action") != "connect":
            raise bad_request("INVALID_STATE", "Invalid state action")

        user_id = state_data.get("user_id")
        if not user_id:
            raise bad_request("INVALID_STATE", "Missing user in state")

        from uuid import UUID
        user = db.get(__import__("app.models.user", fromlist=["User"]).User, UUID(user_id))
        if not user or not user.is_active:
            raise bad_request("INVALID_USER", "User not found")

        connect_redirect_uri = settings.yandex_redirect_uri.replace("/callback", "/connect/callback")
        profile = exchange_yandex_code(
            settings.yandex_client_id,
            settings.yandex_client_secret,
            code,
            connect_redirect_uri,
        )
        connect_oauth_identity(db, user, "yandex", profile)
        db.commit()
        return RedirectResponse(_FE("/security?connected=yandex"), status_code=302)
    except Exception as exc:
        from urllib.parse import quote
        msg = exc.detail["message"] if hasattr(exc, "detail") and isinstance(exc.detail, dict) else str(exc)
        return RedirectResponse(_FE(f"/security?error={quote(msg)}"), status_code=302)
