"""
Telegram Login Widget authentication routes.
Uses HMAC-SHA256 hash verification per Telegram docs.
"""

import hashlib
import hmac
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.cookies import set_refresh_cookie
from app.core.errors import bad_request, unauthorized
from app.db.session import get_db
from app.models.user import User
from app.services.oauth_service import connect_oauth_identity, upsert_oauth_user
from app.services.session_service import create_refresh_session, request_ip, request_user_agent

router = APIRouter(prefix="/auth/telegram", tags=["telegram"])

_MAX_AUTH_AGE = 86400  # 24 hours


def _verify_telegram_hash(data: dict) -> None:
    """Verify Telegram Login Widget data using HMAC-SHA256."""
    if not settings.telegram_bot_token:
        raise bad_request("PROVIDER_DISABLED", "Telegram auth is not configured")

    auth_date = data.get("auth_date")
    if not auth_date:
        raise bad_request("INVALID_DATA", "Missing auth_date")
    if time.time() - int(auth_date) > _MAX_AUTH_AGE:
        raise bad_request("AUTH_EXPIRED", "Telegram auth data has expired")

    received_hash = data.get("hash")
    if not received_hash:
        raise bad_request("INVALID_DATA", "Missing hash")

    # Build check_string: sorted key=value pairs (excluding hash), separated by \n
    fields = {k: v for k, v in data.items() if k != "hash"}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))

    secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
    expected_hash = hmac.new(key=secret_key, msg=check_string.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise bad_request("INVALID_HASH", "Telegram hash verification failed")


def _profile_from_tg(data: dict) -> dict:
    first_name = data.get("first_name", "")
    last_name = data.get("last_name")
    username = data.get("username")
    photo_url = data.get("photo_url")
    return {
        "provider_user_id": str(data["id"]),
        "provider_email": None,
        "name": first_name,
        "last_name": last_name,
        "username": username,
        "avatar_url": photo_url,
    }


@router.post("")
async def telegram_login(request: Request, db: DBSession = Depends(get_db)):
    """Login via Telegram Login Widget callback data."""
    data = await request.json()
    _verify_telegram_hash(data)
    profile = _profile_from_tg(data)
    user, _ = upsert_oauth_user(
        db, "telegram", profile,
        request_ip=request_ip(request),
        request_ua=request_user_agent(request),
    )
    refresh_token, _ = create_refresh_session(db, user, request)
    db.commit()

    from fastapi.responses import JSONResponse
    from app.core.security import create_access_token
    from app.schemas.auth import AuthResponse, UserRead
    response = JSONResponse(
        content=AuthResponse(
            user=UserRead(
                id=user.id,
                email=user.email,
                name=user.name,
                last_name=user.last_name,
                phone=user.phone,
                avatar_url=user.avatar_url,
                role=user.role,
                connected_providers=[i.provider for i in user.identities],
                created_at=user.created_at,
            ),
            access_token=create_access_token(user),
        ).model_dump(mode="json")
    )
    set_refresh_cookie(response, refresh_token)
    return response


@router.post("/connect")
async def telegram_connect(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession = Depends(get_db),
):
    """Connect Telegram to existing account."""
    data = await request.json()
    _verify_telegram_hash(data)
    profile = _profile_from_tg(data)
    connect_oauth_identity(db, current_user, "telegram", profile)
    db.commit()
    return {"ok": True}
