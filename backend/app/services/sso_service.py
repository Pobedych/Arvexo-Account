import secrets
from datetime import timedelta

from sqlalchemy.orm import Session as DBSession

from app.core.errors import bad_request, not_found
from app.core.security import hash_token, utc_now, verify_password
from app.models.oauth_client import OAuthClient
from app.models.sso_code import SSOCode
from app.models.user import User

SSO_CODE_TTL_MINUTES = 5


def get_active_client(db: DBSession, client_id: str) -> OAuthClient:
    client = (
        db.query(OAuthClient)
        .filter(OAuthClient.client_id == client_id, OAuthClient.is_active == True)  # noqa: E712
        .one_or_none()
    )
    if not client:
        raise not_found("CLIENT_NOT_FOUND", "OAuth client not found or inactive")
    return client


def validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> None:
    if redirect_uri not in client.allowed_redirect_uris:
        raise bad_request("INVALID_REDIRECT_URI", "Redirect URI is not allowed")


def create_sso_code(
    db: DBSession,
    user: User,
    client: OAuthClient,
    redirect_uri: str,
    state: str | None,
    scope: str | None = None,
) -> str:
    raw_code = secrets.token_urlsafe(32)
    db.add(
        SSOCode(
            code_hash=hash_token(raw_code),
            user_id=user.id,
            client_id=client.client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            expires_at=utc_now() + timedelta(minutes=SSO_CODE_TTL_MINUTES),
        )
    )
    return raw_code


def exchange_code(
    db: DBSession,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> User:
    client = (
        db.query(OAuthClient)
        .filter(OAuthClient.client_id == client_id, OAuthClient.is_active == True)  # noqa: E712
        .one_or_none()
    )
    if not client or not verify_password(client_secret, client.client_secret_hash):
        raise bad_request("INVALID_CLIENT", "Invalid client credentials")

    sso_code = db.query(SSOCode).filter(SSOCode.code_hash == hash_token(code)).one_or_none()
    if sso_code is None:
        raise bad_request("INVALID_CODE", "Invalid or expired code")

    now = utc_now()
    expires_at = sso_code.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)

    if sso_code.used_at is not None:
        raise bad_request("CODE_ALREADY_USED", "Code has already been used")
    if expires_at <= now:
        raise bad_request("CODE_EXPIRED", "Code has expired")
    if sso_code.client_id != client_id:
        raise bad_request("CLIENT_MISMATCH", "Code was not issued for this client")
    if sso_code.redirect_uri != redirect_uri:
        raise bad_request("REDIRECT_URI_MISMATCH", "Redirect URI does not match")

    sso_code.used_at = now

    user = db.get(User, sso_code.user_id)
    if not user or not user.is_active or user.is_banned:
        raise bad_request("INVALID_USER", "User is not available")

    return user
