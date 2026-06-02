import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.finding import Finding, FindingStatus
from app.models.user import User
from app.schemas.observation_finding import FindingCreate, FindingUpdate
from app.services.audit_service import log_audit_event

class FindingService:
    # State transitions
    VALID_TRANSITIONS = {
        FindingStatus.POTENTIAL: [FindingStatus.VERIFIED, FindingStatus.CLOSED, FindingStatus.SUPPRESSED],
        FindingStatus.VERIFIED: [FindingStatus.ASSIGNED, FindingStatus.FIXED, FindingStatus.CLOSED, FindingStatus.SUPPRESSED],
        FindingStatus.ASSIGNED: [FindingStatus.IN_PROGRESS, FindingStatus.FIXED, FindingStatus.CLOSED],
        FindingStatus.IN_PROGRESS: [FindingStatus.FIXED, FindingStatus.ASSIGNED, FindingStatus.CLOSED],
        FindingStatus.FIXED: [FindingStatus.RETEST_PENDING, FindingStatus.CLOSED],
        FindingStatus.RETEST_PENDING: [FindingStatus.VERIFIED, FindingStatus.CLOSED],
        FindingStatus.CLOSED: [FindingStatus.VERIFIED], # Reopen
        FindingStatus.SUPPRESSED: [FindingStatus.POTENTIAL]
    }

    @staticmethod
    def create_finding(db: Session, obj_in: FindingCreate, user: User, request: Request = None) -> Finding:
        db_obj = Finding(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        log_audit_event(
            db=db,
            org_id=db_obj.org_id,
            user=user,
            action="finding.created",
            resource_type="finding",
            resource_id=str(db_obj.id),
            request=request
        )

        return db_obj

    @staticmethod
    def update_finding_status(db: Session, org_id: uuid.UUID, finding_id: uuid.UUID, new_status: FindingStatus, user: User, request: Request = None) -> Finding:
        db_obj = db.query(Finding).filter(Finding.org_id == org_id, Finding.id == finding_id).first()
        if not db_obj:
            raise ValueError("Finding not found")

        if new_status not in FindingService.VALID_TRANSITIONS.get(db_obj.status, []):
            raise ValueError(f"Invalid transition from {db_obj.status} to {new_status}")

        db_obj.status = new_status
        db.commit()
        db.refresh(db_obj)

        log_audit_event(
            db=db,
            org_id=db_obj.org_id,
            user=user,
            action="finding.status_changed",
            resource_type="finding",
            resource_id=str(db_obj.id),
            request=request
        )

        return db_obj

    @staticmethod
    def get_finding(db: Session, org_id: uuid.UUID, id: uuid.UUID) -> Optional[Finding]:
        return db.query(Finding).filter(Finding.org_id == org_id, Finding.id == id).first()

    @staticmethod
    def get_findings(db: Session, org_id: uuid.UUID) -> List[Finding]:
        return db.query(Finding).filter(Finding.org_id == org_id).all()
