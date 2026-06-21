from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.errors import bad_request, not_found
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, IdentityRead, UpdateProfileRequest, UserRead
from app.services.audit_service import write_audit
from app.services.auth_service import user_to_read, validate_password_strength

router = APIRouter(prefix="/account", tags=["account"])


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> UserRead:
    if payload.name is not None:
        current_user.name = payload.name or None
    if payload.last_name is not None:
        current_user.last_name = payload.last_name or None
    if payload.phone is not None:
        current_user.phone = payload.phone or None
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url or None
    db.commit()
    db.refresh(current_user)
    return user_to_read(current_user)


@router.post("/password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> dict[str, bool]:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise bad_request("INVALID_CURRENT_PASSWORD", "Неверный текущий пароль")
    validate_password_strength(payload.new_password)
    current_user.password_hash = hash_password(payload.new_password)
    write_audit(db, "password_changed", user_id=current_user.id)
    db.commit()
    return {"ok": True}


@router.get("/identities", response_model=list[IdentityRead])
def list_identities(
    current_user: User = Depends(get_current_user),
) -> list[IdentityRead]:
    return [
        IdentityRead(
            provider=identity.provider,
            provider_email=identity.provider_email,
            created_at=identity.created_at,
        )
        for identity in current_user.identities
    ]


@router.delete("/identities/{provider}")
def disconnect_identity(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> dict[str, bool]:
    identity = next((i for i in current_user.identities if i.provider == provider), None)
    if identity is None:
        raise not_found("IDENTITY_NOT_FOUND", "Способ входа не найден")
    if len(current_user.identities) <= 1:
        raise bad_request("LAST_IDENTITY", "Нельзя отвязать последний способ входа")
    db.delete(identity)
    write_audit(db, "disconnect_provider", user_id=current_user.id, provider=provider)
    db.commit()
    return {"ok": True}
