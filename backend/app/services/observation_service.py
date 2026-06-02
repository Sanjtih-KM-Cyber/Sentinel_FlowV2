import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import Request
from app.models.observation import Observation
from app.models.user import User
from app.schemas.observation_finding import ObservationCreate
from app.services.audit_service import log_audit_event

class ObservationService:
    @staticmethod
    def create_or_get_observation(db: Session, obj_in: ObservationCreate, user: User, request: Request = None) -> Observation:
        existing = db.query(Observation).filter(
            Observation.org_id == obj_in.org_id,
            Observation.asset_id == obj_in.asset_id,
            Observation.observation_type == obj_in.observation_type,
            Observation.fingerprint == obj_in.fingerprint
        ).first()

        if existing:
            return existing

        db_obj = Observation(**obj_in.model_dump())
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
            
            log_audit_event(
                db=db,
                org_id=db_obj.org_id,
                user=user,
                action="observation.created",
                resource_type="observation",
                resource_id=str(db_obj.id),
                request=request
            )
            return db_obj
        except IntegrityError:
            db.rollback()
            return db.query(Observation).filter(
                Observation.org_id == obj_in.org_id,
                Observation.asset_id == obj_in.asset_id,
                Observation.observation_type == obj_in.observation_type,
                Observation.fingerprint == obj_in.fingerprint
            ).first()

    @staticmethod
    def get_observation(db: Session, org_id: uuid.UUID, id: uuid.UUID) -> Optional[Observation]:
        return db.query(Observation).filter(Observation.org_id == org_id, Observation.id == id).first()

    @staticmethod
    def get_observations(db: Session, org_id: uuid.UUID) -> List[Observation]:
        return db.query(Observation).filter(Observation.org_id == org_id).all()
