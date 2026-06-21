"""
Internal SSO for Arvexo services (Authorization Code-like flow).

Flow:
  1. Service redirects user to GET /sso/start?client_id=...&redirect_uri=...&state=...
  2. Backend validates params, checks auth cookie:
     - Not authenticated → redirect to frontend /login?next=/sso/continue?...
     - Authenticated     → redirect to frontend /sso/continue?...
  3. Frontend /sso/continue shows consent page; user confirms.
  4. Frontend POSTs /sso/confirm (with Bearer token) → receives redirect_url.
  5. Frontend does window.location = redirect_url
     → Service gets ?code=...&state=...
  6. Service POSTs /sso/exchange (server-to-server) → gets account_user.
"""

from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.cookies import REFRESH_COOKIE_NAME
from app.core.security import hash_token
from app.db.session import get_db
from app.models.session import Session as DBSessionModel
from app.models.user import User
from app.schemas.auth import (
    SSOClientInfo,
    SSOConfirmRequest,
    SSOConfirmResponse,
    SSOExchangeRequest,
    SSOExchangeResponse,
    SSOUserPublic,
)
from app.services.audit_service import write_audit
from app.services.sso_service import (
    SSO_CODE_TTL_MINUTES,
    create_sso_code,
    exchange_code,
    get_active_client,
    validate_redirect_uri,
)
from app.services.session_service import get_valid_refresh_session

router = APIRouter(prefix="/sso", tags=["sso"])


def _authed_user(refresh_token: str | None, db: DBSession) -> User | None:
    if not refresh_token:
        return None
    session = get_valid_refresh_session(db, refresh_token)
    if not session:
        return None
    user = session.user
    if not user or not user.is_active or user.is_banned:
        return None
    return user


@router.get("/start")
def sso_start(
    client_id: str,
    redirect_uri: str,
    state: str | None = None,
    scope: str | None = None,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: DBSession = Depends(get_db),
) -> RedirectResponse:
    client = get_active_client(db, client_id)
    validate_redirect_uri(client, redirect_uri)

    continue_params = {"client_id": client_id, "redirect_uri": redirect_uri}
    if state:
        continue_params["state"] = state
    if scope:
        continue_params["scope"] = scope

    continue_url = f"{settings.frontend_url.rstrip('/')}/sso/continue?{urlencode(continue_params)}"

    user = _authed_user(refresh_token, db)
    if user is None:
        login_url = f"{settings.frontend_url.rstrip('/')}/login?{urlencode({'next': continue_url})}"
        return RedirectResponse(url=login_url, status_code=302)

    return RedirectResponse(url=continue_url, status_code=302)


@router.get("/client", response_model=SSOClientInfo)
def sso_client_info(
    client_id: str,
    db: DBSession = Depends(get_db),
) -> SSOClientInfo:
    client = get_active_client(db, client_id)
    return SSOClientInfo(client_id=client.client_id, name=client.name)


@router.post("/confirm", response_model=SSOConfirmResponse)
def sso_confirm(
    payload: SSOConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> SSOConfirmResponse:
    client = get_active_client(db, payload.client_id)
    validate_redirect_uri(client, payload.redirect_uri)

    raw_code = create_sso_code(
        db,
        current_user,
        client,
        payload.redirect_uri,
        payload.state,
        payload.scope,
    )
    write_audit(
        db,
        "sso_authorize",
        user_id=current_user.id,
        metadata={"client_id": payload.client_id},
    )
    db.commit()

    params: dict[str, str] = {"code": raw_code}
    if payload.state:
        params["state"] = payload.state
    redirect_url = f"{payload.redirect_uri}?{urlencode(params)}"
    return SSOConfirmResponse(redirect_url=redirect_url)


@router.post("/exchange", response_model=SSOExchangeResponse)
def sso_exchange(
    payload: SSOExchangeRequest,
    db: DBSession = Depends(get_db),
) -> SSOExchangeResponse:
    user = exchange_code(db, payload.client_id, payload.client_secret, payload.code, payload.redirect_uri)
    write_audit(
        db,
        "sso_token_exchange",
        user_id=user.id,
        metadata={"client_id": payload.client_id},
    )
    db.commit()

    return SSOExchangeResponse(
        account_user=SSOUserPublic(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
        ),
        expires_in=SSO_CODE_TTL_MINUTES * 60,
    )
