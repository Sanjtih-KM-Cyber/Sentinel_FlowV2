import uuid
import hashlib
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.evidence import Evidence, EvidenceType

class EvidenceService:
    @staticmethod
    def generate_content_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def store_evidence(db: Session, org_id: uuid.UUID, evidence_type: EvidenceType, content: str, storage_path: str = None) -> Evidence:
        """
        Stores evidence, ensuring deduplication via content hash.
        """
        content_hash = EvidenceService.generate_content_hash(content)
        
        existing = db.query(Evidence).filter(
            Evidence.org_id == org_id,
            Evidence.content_hash == content_hash
        ).first()

        if existing:
            return existing

        snippet = content[:1000] if content else None # truncate snippet
        
        db_obj = Evidence(
            org_id=org_id,
            evidence_type=evidence_type,
            content_hash=content_hash,
            storage_path=storage_path,
            snippet=snippet
        )
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            return db.query(Evidence).filter(
                Evidence.org_id == org_id,
                Evidence.content_hash == content_hash
            ).first()

    @staticmethod
    def validate_integrity(db: Session, evidence_id: uuid.UUID, current_content: str) -> str:
        """
        Validates the integrity of the evidence by comparing the hash of current_content
        with the stored content_hash. Returns 'valid' or 'invalid' and persists the result.
        """
        ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not ev:
            raise ValueError("Evidence not found")
        
        current_hash = EvidenceService.generate_content_hash(current_content)
        status = "valid" if current_hash == ev.content_hash else "invalid"
        
        ev.validation_status = status
        db.commit()
        db.refresh(ev)
        
        return status

    @staticmethod
    def get_evidence(db: Session, org_id: uuid.UUID, id: uuid.UUID) -> Optional[Evidence]:
        return db.query(Evidence).filter(Evidence.org_id == org_id, Evidence.id == id).first()

    @staticmethod
    def get_all_evidence(db: Session, org_id: uuid.UUID) -> List[Evidence]:
        return db.query(Evidence).filter(Evidence.org_id == org_id).all()
