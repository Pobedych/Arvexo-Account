from datetime import timedelta

from fastapi import Request
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import generate_refresh_token, hash_token, utc_now
from app.models.session import Session
from app.models.user import User


def request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def request_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def create_refresh_session(db: DBSession, user: User, request: Request) -> tuple[str, Session]:
    token = generate_refresh_token()
    session = Session(
        user_id=user.id,
        refresh_token_hash=hash_token(token),
        user_agent=request_user_agent(request),
        ip_address=request_ip(request),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_ttl_days),
    )
    db.add(session)
    return token, session


def get_valid_refresh_session(db: DBSession, token: str) -> Session | None:
    session = db.query(Session).filter(Session.refresh_token_hash == hash_token(token)).one_or_none()
    if not session:
        return None
    now = utc_now()
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)
    if session.revoked_at or expires_at <= now:
        return None
    return session


def revoke_session(session: Session) -> None:
    session.revoked_at = utc_now()
