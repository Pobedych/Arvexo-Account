from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    action: str,
    user_id: UUID | None = None,
    provider: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            provider=provider,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_data=metadata,
        )
    )
