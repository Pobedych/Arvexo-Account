from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user, get_refresh_cookie
from app.core.config import settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.errors import unauthorized
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, OAuthStatusResponse, RefreshResponse, RegisterRequest, UserRead
from app.services.audit_service import write_audit
from app.services.auth_service import authenticate_email_user, register_email_user, user_to_read
from app.services.session_service import create_refresh_session, get_valid_refresh_session, request_ip, request_user_agent, revoke_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/providers", response_model=OAuthStatusResponse)
def providers() -> OAuthStatusResponse:
    return OAuthStatusResponse(**settings.oauth_enabled)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, request: Request, response: Response, db: DBSession = Depends(get_db)) -> AuthResponse:
    user = register_email_user(db, payload.email, payload.password, payload.name, request)
    refresh_token, _ = create_refresh_session(db, user, request)
    access_token = create_access_token(user)
    db.commit()
    db.refresh(user)
    set_refresh_cookie(response, refresh_token)
    return AuthResponse(user=user_to_read(user), access_token=access_token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: DBSession = Depends(get_db)) -> AuthResponse:
    user = authenticate_email_user(db, payload.email, payload.password, request)
    refresh_token, _ = create_refresh_session(db, user, request)
    access_token = create_access_token(user)
    db.commit()
    db.refresh(user)
    set_refresh_cookie(response, refresh_token)
    return AuthResponse(user=user_to_read(user), access_token=access_token)


@router.post("/refresh", response_model=RefreshResponse)
def refresh(refresh_token: str = Depends(get_refresh_cookie), db: DBSession = Depends(get_db)) -> RefreshResponse:
    session = get_valid_refresh_session(db, refresh_token)
    if not session:
        raise unauthorized("Refresh session expired")
    user = session.user
    if not user or not user.is_active or user.is_banned:
        raise unauthorized("Invalid user")
    write_audit(db, "refresh", user_id=user.id)
    access_token = create_access_token(user)
    db.commit()
    return RefreshResponse(access_token=access_token)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    refresh_token: str = Depends(get_refresh_cookie),
    db: DBSession = Depends(get_db),
) -> dict[str, bool]:
    session = get_valid_refresh_session(db, refresh_token)
    if session:
        revoke_session(session)
        write_audit(
            db,
            "logout",
            user_id=session.user_id,
            ip_address=request_ip(request),
            user_agent=request_user_agent(request),
        )
        db.commit()
    clear_refresh_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return user_to_read(current_user)
