from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session as DBSession

from app.core.cookies import REFRESH_COOKIE_NAME
from app.core.errors import unauthorized
from app.core.security import hash_token, user_id_from_token
from app.db.session import get_db
from app.models.session import Session
from app.models.user import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized()
    token = authorization.split(" ", 1)[1].strip()
    user_id = user_id_from_token(token)
    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_banned:
        raise unauthorized("Invalid user")
    return user


def get_refresh_cookie(arvexo_account_refresh: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME)) -> str:
    if not arvexo_account_refresh:
        raise unauthorized("Refresh session required")
    return arvexo_account_refresh


def get_current_session_id(
    arvexo_account_refresh: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: DBSession = Depends(get_db),
) -> UUID | None:
    if not arvexo_account_refresh:
        return None
    session = db.query(Session).filter(
        Session.refresh_token_hash == hash_token(arvexo_account_refresh)
    ).one_or_none()
    return session.id if session else None
