from fastapi import Request
from sqlalchemy.orm import Session as DBSession

from app.core.errors import bad_request, conflict, forbidden, invalid_credentials
from app.core.security import hash_password, verify_password
from app.models.auth_identity import AuthIdentity
from app.models.mixins import utc_now
from app.models.user import User
from app.schemas.auth import UserRead
from app.services.audit_service import write_audit
from app.services.session_service import request_ip, request_user_agent


def user_to_read(user: User) -> UserRead:
    providers = sorted({identity.provider for identity in user.identities})
    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        connected_providers=providers,
        created_at=user.created_at,
    )


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise bad_request("WEAK_PASSWORD", "Password must contain at least 8 characters")


def register_email_user(db: DBSession, email: str, password: str, name: str | None, request: Request) -> User:
    normalized_email = email.lower()
    if db.query(User).filter(User.email == normalized_email).one_or_none():
        raise conflict("EMAIL_ALREADY_EXISTS", "Email is already registered")
    validate_password_strength(password)
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        name=name,
        role="user",
        last_login_at=utc_now(),
    )
    db.add(user)
    db.flush()
    db.add(AuthIdentity(user_id=user.id, provider="email", provider_user_id=normalized_email, provider_email=normalized_email))
    write_audit(
        db,
        "register",
        user_id=user.id,
        provider="email",
        ip_address=request_ip(request),
        user_agent=request_user_agent(request),
    )
    return user


def authenticate_email_user(db: DBSession, email: str, password: str, request: Request) -> User:
    normalized_email = email.lower()
    user = db.query(User).filter(User.email == normalized_email).one_or_none()
    if not user or not verify_password(password, user.password_hash):
        write_audit(
            db,
            "login_failed",
            provider="email",
            ip_address=request_ip(request),
            user_agent=request_user_agent(request),
            metadata={"email": normalized_email},
        )
        raise invalid_credentials()
    if not user.is_active:
        raise forbidden("USER_INACTIVE", "User is inactive")
    if user.is_banned:
        raise forbidden("USER_BANNED", "User is banned")
    user.last_login_at = utc_now()
    write_audit(
        db,
        "login_success",
        user_id=user.id,
        provider="email",
        ip_address=request_ip(request),
        user_agent=request_user_agent(request),
    )
    return user
