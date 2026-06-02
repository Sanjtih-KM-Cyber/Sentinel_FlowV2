from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from app.repositories.base import CRUDBase

class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogCreate]):
    def get_by_org(
        self, db: Session, *, org_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

audit_log = CRUDAuditLog(AuditLog)
