import uuid
from sqlalchemy.orm import Session
from app.models.confidence_score import ConfidenceScore, ConfidenceLevel
from app.schemas.observation_finding import ConfidenceScoreCreate

class ConfidenceService:
    @staticmethod
    def add_confidence_score(db: Session, obj_in: ConfidenceScoreCreate) -> ConfidenceScore:
        db_obj = ConfidenceScore(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_effective_confidence(db: Session, org_id: uuid.UUID, finding_id: uuid.UUID) -> ConfidenceScore:
        return db.query(ConfidenceScore).filter(
            ConfidenceScore.org_id == org_id,
            ConfidenceScore.finding_id == finding_id
        ).order_by(ConfidenceScore.created_at.desc()).first()
