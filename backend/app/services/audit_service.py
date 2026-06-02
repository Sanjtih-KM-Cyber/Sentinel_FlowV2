import uuid
from fastapi import Request
from sqlalchemy.orm import Session
from app.schemas.audit_log import AuditLogCreate
from app.repositories.audit_log import audit_log
from app.models.user import User

def log_audit_event(
    db: Session,
    *,
    org_id: uuid.UUID,
    user: User,
    action: str,
    resource_type: str,
    resource_id: str = None,
    request: Request = None,
    commit: bool = True
) -> None:
    ip_address = None
    user_agent = None

    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                ip_address = real_ip.strip()
            else:
                ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log_in = AuditLogCreate(
        org_id=org_id,
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    audit_log.create(db=db, obj_in=log_in, commit=commit)
