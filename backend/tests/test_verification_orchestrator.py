import pytest
import datetime
from sqlalchemy.orm import Session
from app.services.verification_orchestrator import VerificationService
from app.services.verification_framework import BaseVerificationRule
from app.models.observation import Observation, ObservationType
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.models.confidence_score import ConfidenceLevel
from app.models.verification_run import VerificationStatus
from app.services.observation_service import ObservationService
from app.schemas.observation_finding import ObservationCreate, ConfidenceScoreBase
from typing import List

class DummyVerificationRule(BaseVerificationRule):
    @property
    def rule_id(self) -> str:
        return "dummy-rule-01"
        
    def observation_criteria(self) -> List[str]:
        return [ObservationType.SERVER_ERROR]
        
    def evidence_requirements(self) -> List[str]:
        return [EvidenceType.RESPONSE]
        
    async def verify(self, db: Session, observation: Observation, evidence_list: List[Evidence]) -> bool:
        if any("fail" in (e.snippet or "") for e in evidence_list):
            raise ValueError("Intentional verification failure")
        return True
        
    def calculate_confidence(self, observation: Observation, evidence_list: List[Evidence], verified: bool) -> ConfidenceScoreBase:
        return ConfidenceScoreBase(
            level=ConfidenceLevel.HIGH,
            score_numerical=0.9,
            reasoning="Dummy reasoning"
        )

@pytest.mark.asyncio
async def test_verification_orchestrator_success(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["admin1"]

    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="verifysuccess.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    obs_in = ObservationCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_type=ObservationType.SERVER_ERROR, title="Error", fingerprint="fp_verify_sfc")
    obs = ObservationService.create_or_get_observation(db_session, obs_in, user)

    ev = Evidence(org_id=org_id, evidence_type=EvidenceType.RESPONSE, content_hash="dummyhash123", snippet="clean data")
    db_session.add(ev)
    db_session.commit()

    orchestrator = VerificationService(rules=[DummyVerificationRule()])
    await orchestrator.execute_verification(db_session, obs, [ev], user)

    # Check Verification Run
    from app.models.verification_run import VerificationRun
    run = db_session.query(VerificationRun).filter(VerificationRun.observation_id == obs.id).first()
    assert run is not None
    assert run.status == VerificationStatus.COMPLETED
    assert run.rule_id == "dummy-rule-01"

    # Check Audit events
    from app.models.audit_log import AuditLog
    logs = db_session.query(AuditLog).filter(AuditLog.resource_id == str(run.id)).order_by(AuditLog.created_at.asc()).all()
    assert len(logs) == 2
    assert logs[0].action == "verification.started"
    assert logs[1].action == "verification.completed"
    
    # Check Finding and Confidence
    from app.models.finding import Finding, FindingStatus
    finding = db_session.query(Finding).filter(Finding.observation_id == obs.id).first()
    assert finding is not None
    assert finding.status == FindingStatus.VERIFIED
    
    from app.models.confidence_score import ConfidenceScore
    conf = db_session.query(ConfidenceScore).filter(ConfidenceScore.finding_id == finding.id).first()
    assert conf is not None
    assert conf.level == ConfidenceLevel.HIGH
    assert conf.score_numerical == 0.9

@pytest.mark.asyncio
async def test_verification_orchestrator_failure(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["admin1"]

    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="verifyfail.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    obs_in = ObservationCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_type=ObservationType.SERVER_ERROR, title="Error f", fingerprint="fp_verify_fail")
    obs = ObservationService.create_or_get_observation(db_session, obs_in, user)

    ev = Evidence(org_id=org_id, evidence_type=EvidenceType.RESPONSE, content_hash="dummyhash124", snippet="containsfail string")
    db_session.add(ev)
    db_session.commit()

    orchestrator = VerificationService(rules=[DummyVerificationRule()])
    await orchestrator.execute_verification(db_session, obs, [ev], user)

    # Check Verification Run
    from app.models.verification_run import VerificationRun
    run = db_session.query(VerificationRun).filter(VerificationRun.observation_id == obs.id).first()
    assert run.status == VerificationStatus.FAILED
    assert "Intentional verification failure" in run.error_message
