"""
Telegram OIDC routes (authorization_code + PKCE).
Uses https://id.telegram.org/.well-known/openid-configuration
"""

import base64
import hashlib
import secrets
from typing import Annotated
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import RedirectResponse
from jwt import PyJWKClient
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.cookies import REFRESH_COOKIE_NAME, set_refresh_cookie
from app.core.errors import bad_request
from app.core.security import create_oauth_state, decode_oauth_state
from app.db.session import get_db
from app.models.user import User
from app.services.oauth_service import connect_oauth_identity, upsert_oauth_user
from app.services.session_service import (
    create_refresh_session,
    get_valid_refresh_session,
    request_ip,
    request_user_agent,
)

import httpx

router = APIRouter(prefix="/auth/telegram", tags=["telegram"])

_TELEGRAM_AUTH_URL = "https://oauth.telegram.org/auth"
_TELEGRAM_TOKEN_URL = "https://oauth.telegram.org/token"
_TELEGRAM_JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
_TELEGRAM_ISSUER = "https://oauth.telegram.org"

_jwks_client = PyJWKClient(_TELEGRAM_JWKS_URL, cache_keys=True)

_FE = lambda path: f"{settings.frontend_url.rstrip('/')}{path}"  # noqa: E731


def _bot_id() -> str:
    """Extract numeric bot ID from token (format: {id}:{secret})."""
    return settings.telegram_bot_token.split(":")[0]


def _pkce_pair() -> tuple[str, str]:
    """Generate (code_verifier, code_challenge_S256) pair."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def _build_auth_url(redirect_uri: str, state: str, code_challenge: str) -> str:
    return _TELEGRAM_AUTH_URL + "?" + urlencode({
        "client_id": _bot_id(),
        "response_type": "code",
        "scope": "openid profile",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })


def _exchange_code(code: str, redirect_uri: str, code_verifier: str) -> dict:
    """Exchange authorization code for tokens at Telegram's token endpoint."""
    with httpx.Client(timeout=10) as http:
        resp = http.post(
            _TELEGRAM_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": _bot_id(),
                "client_secret": settings.telegram_bot_token,
                "code_verifier": code_verifier,
            },
        )
    if resp.status_code != 200:
        raise bad_request("TELEGRAM_TOKEN_ERROR", f"Telegram token exchange failed: {resp.text}")
    return resp.json()


def _verify_id_token(id_token: str) -> dict:
    """Verify Telegram id_token using JWKS and return claims."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "ES256", "EdDSA", "ES256K"],
            audience=_bot_id(),
            issuer=_TELEGRAM_ISSUER,
        )
        return payload
    except jwt.PyJWTError as exc:
        raise bad_request("TELEGRAM_TOKEN_INVALID", f"Invalid Telegram id_token: {exc}") from exc


def _profile_from_claims(claims: dict) -> dict:
    name_parts = (claims.get("name") or "").split(" ", 1)
    return {
        "provider_user_id": str(claims["sub"]),
        "provider_email": None,
        "name": name_parts[0] if name_parts else None,
        "last_name": name_parts[1] if len(name_parts) > 1 else None,
        "avatar_url": claims.get("picture"),
    }


# ── Login flow ───────────────────────────────────────────────────────────────

@router.get("")
def telegram_login() -> RedirectResponse:
    if not settings.oauth_enabled["telegram"]:
        raise bad_request("PROVIDER_DISABLED", "Telegram OIDC is not configured")
    code_verifier, code_challenge = _pkce_pair()
    state = create_oauth_state("login", extra={"cv": code_verifier})
    return RedirectResponse(
        _build_auth_url(settings.telegram_redirect_uri, state, code_challenge),
        status_code=302,
    )


@router.get("/callback")
def telegram_callback(
    code: str,
    state: str,
    request: Request,
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    try:
        state_data = decode_oauth_state(state)
        if state_data.get("action") != "login":
            raise bad_request("INVALID_STATE", "Invalid state action")

        code_verifier = state_data.get("extra", {}).get("cv", "")
        tokens = _exchange_code(code, settings.telegram_redirect_uri, code_verifier)
        claims = _verify_id_token(tokens["id_token"])
        profile = _profile_from_claims(claims)

        user, _ = upsert_oauth_user(
            db, "telegram", profile,
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


# ── Connect flow ─────────────────────────────────────────────────────────────

@router.get("/connect")
def telegram_connect(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    if not settings.oauth_enabled["telegram"]:
        raise bad_request("PROVIDER_DISABLED", "Telegram OIDC is not configured")

    session = get_valid_refresh_session(db, refresh_token) if refresh_token else None
    if not session or not session.user:
        return RedirectResponse(_FE("/login"), status_code=302)

    code_verifier, code_challenge = _pkce_pair()
    state = create_oauth_state("connect", user_id=str(session.user.id), extra={"cv": code_verifier})
    connect_uri = settings.telegram_redirect_uri.replace("/callback", "/connect/callback")
    return RedirectResponse(
        _build_auth_url(connect_uri, state, code_challenge),
        status_code=302,
    )


@router.get("/connect/callback")
def telegram_connect_callback(
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

        code_verifier = state_data.get("extra", {}).get("cv", "")
        connect_uri = settings.telegram_redirect_uri.replace("/callback", "/connect/callback")
        tokens = _exchange_code(code, connect_uri, code_verifier)
        claims = _verify_id_token(tokens["id_token"])
        profile = _profile_from_claims(claims)

        connect_oauth_identity(db, user, "telegram", profile)
        db.commit()
        return RedirectResponse(_FE("/security?connected=telegram"), status_code=302)
    except Exception as exc:
        from urllib.parse import quote
        msg = exc.detail["message"] if hasattr(exc, "detail") and isinstance(exc.detail, dict) else str(exc)
        return RedirectResponse(_FE(f"/security?error={quote(msg)}"), status_code=302)
