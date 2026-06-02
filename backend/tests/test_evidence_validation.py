import pytest
from sqlalchemy.orm import Session
from app.services.evidence_service import EvidenceService
from app.models.evidence import EvidenceType

def test_evidence_integrity_valid(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    content = "Original Content for verification"
    
    ev = EvidenceService.store_evidence(db_session, org_id, EvidenceType.RESPONSE, content)
    assert ev.validation_status is None
    
    status = EvidenceService.validate_integrity(db_session, ev.id, content)
    assert status == "valid"
    assert ev.validation_status == "valid"

def test_evidence_integrity_invalid(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    content = "Original Content for tampering"
    
    ev = EvidenceService.store_evidence(db_session, org_id, EvidenceType.RESPONSE, content)
    
    tampered_content = "Tampered Content"
    status = EvidenceService.validate_integrity(db_session, ev.id, tampered_content)
    assert status == "invalid"
    assert ev.validation_status == "invalid"
