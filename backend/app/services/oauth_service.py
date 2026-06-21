"""
OAuth provider integrations (Yandex).
Handles code exchange and profile normalization.
"""

import httpx
from sqlalchemy.orm import Session as DBSession

from app.core.errors import bad_request, conflict
from app.models.auth_identity import AuthIdentity
from app.models.mixins import utc_now
from app.models.user import User
from app.services.audit_service import write_audit

YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_URL = "https://login.yandex.ru/info?format=json"


def _yandex_avatar(avatar_id: str | None) -> str | None:
    if not avatar_id or avatar_id == "0":
        return None
    return f"https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"


def exchange_yandex_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for Yandex access token + user profile."""
    with httpx.Client(timeout=10) as http:
        token_resp = http.post(
            YANDEX_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
        )
    if token_resp.status_code != 200:
        raise bad_request("YANDEX_TOKEN_ERROR", "Failed to exchange Yandex authorization code")
    access_token = token_resp.json().get("access_token")
    if not access_token:
        raise bad_request("YANDEX_TOKEN_ERROR", "No access token in Yandex response")

    with httpx.Client(timeout=10) as http:
        info_resp = http.get(YANDEX_USER_URL, headers={"Authorization": f"OAuth {access_token}"})
    if info_resp.status_code != 200:
        raise bad_request("YANDEX_USERINFO_ERROR", "Failed to fetch Yandex user info")

    info = info_resp.json()
    return {
        "provider_user_id": str(info["id"]),
        "provider_email": info.get("default_email"),
        "name": info.get("first_name") or info.get("display_name"),
        "last_name": info.get("last_name"),
        "avatar_url": _yandex_avatar(info.get("default_avatar_id")),
    }


def upsert_oauth_user(db: DBSession, provider: str, profile: dict, request_ip: str | None = None, request_ua: str | None = None) -> tuple[User, bool]:
    """
    Find or create a user for an OAuth provider profile.
    Returns (user, is_new).
    Raises conflict if the identity is linked to a different account.
    """
    provider_user_id = profile["provider_user_id"]
    provider_email = profile.get("provider_email")

    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == provider, AuthIdentity.provider_user_id == provider_user_id)
        .one_or_none()
    )

    if identity:
        user = identity.user
        if not user.is_active or user.is_banned:
            raise bad_request("USER_INACTIVE", "Этот аккаунт неактивен или заблокирован")
        # Update email/avatar if changed
        if provider_email and identity.provider_email != provider_email:
            identity.provider_email = provider_email
        write_audit(db, "login_success", user_id=user.id, provider=provider, ip_address=request_ip, user_agent=request_ua)
        return user, False

    # No existing identity — create new user
    user = User(
        email=provider_email,
        name=profile.get("name"),
        last_name=profile.get("last_name"),
        avatar_url=profile.get("avatar_url"),
        role="user",
        last_login_at=utc_now(),
    )
    db.add(user)
    db.flush()
    db.add(AuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=provider_email,
    ))
    write_audit(db, "register", user_id=user.id, provider=provider, ip_address=request_ip, user_agent=request_ua)
    return user, True


def connect_oauth_identity(db: DBSession, user: User, provider: str, profile: dict) -> None:
    """Link a provider identity to an existing user account."""
    provider_user_id = profile["provider_user_id"]

    existing = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == provider, AuthIdentity.provider_user_id == provider_user_id)
        .one_or_none()
    )
    if existing:
        if existing.user_id != user.id:
            raise conflict("IDENTITY_TAKEN", "Этот аккаунт уже привязан к другому пользователю Arvexo")
        return  # already connected to this user

    db.add(AuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=profile.get("provider_email"),
    ))
    write_audit(db, "connect_provider", user_id=user.id, provider=provider)
