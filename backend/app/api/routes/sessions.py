from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_session_id, get_current_user
from app.core.errors import not_found
from app.core.security import utc_now
from app.db.session import get_db
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import SessionRead
from app.services.audit_service import write_audit
from app.services.session_service import revoke_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _active_sessions(user: User) -> list[Session]:
    now = utc_now()
    result = []
    for s in user.sessions:
        expires_at = s.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        if s.revoked_at is None and expires_at > now:
            result.append(s)
    return result


@router.get("", response_model=list[SessionRead])
def get_sessions(
    current_user: User = Depends(get_current_user),
    current_session_id: UUID | None = Depends(get_current_session_id),
) -> list[SessionRead]:
    sessions = _active_sessions(current_user)
    return [
        SessionRead(
            id=s.id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            expires_at=s.expires_at,
            current=s.id == current_session_id,
        )
        for s in sorted(sessions, key=lambda x: x.created_at, reverse=True)
    ]


@router.delete("/{session_id}")
def revoke_one_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> dict[str, bool]:
    session = next((s for s in current_user.sessions if s.id == session_id), None)
    if session is None:
        raise not_found("SESSION_NOT_FOUND", "Сессия не найдена")
    revoke_session(session)
    write_audit(db, "session_revoked", user_id=current_user.id)
    db.commit()
    return {"ok": True}


@router.delete("")
def revoke_other_sessions(
    current_user: User = Depends(get_current_user),
    current_session_id: UUID | None = Depends(get_current_session_id),
    db: DBSession = Depends(get_db),
) -> dict[str, int]:
    sessions = _active_sessions(current_user)
    count = 0
    for s in sessions:
        if s.id != current_session_id:
            revoke_session(s)
            count += 1
    if count:
        write_audit(db, "session_revoked", user_id=current_user.id, metadata={"count": count})
        db.commit()
    return {"revoked": count}
