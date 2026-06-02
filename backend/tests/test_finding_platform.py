import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.orm import Session
from app.core.config import settings
from tests.fixtures import setup_data, get_token
from app.schemas.observation_finding import ObservationCreate, FindingCreate, ConfidenceScoreCreate
from app.models.observation import ObservationType
from app.models.finding import FindingStatus, Severity
from app.models.evidence import EvidenceType
from app.models.confidence_score import ConfidenceLevel
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.finding_service import FindingService
from app.services.confidence_service import ConfidenceService

def test_observation_deduplication(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    from app.models.asset import Asset, AssetType, AssetStatus
    
    asset = Asset(org_id=org_id, project_id=project_id, name="obs.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    obs_in = ObservationCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_type=ObservationType.DNS_MISCONFIGURATION,
        title="Test Observation",
        fingerprint="fp123"
    )

    obs1 = ObservationService.create_or_get_observation(db_session, obs_in, setup_data["admin1"])
    obs2 = ObservationService.create_or_get_observation(db_session, obs_in, setup_data["admin1"])

    assert obs1.id == obs2.id

    obs_in2 = ObservationCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_type=ObservationType.DNS_MISCONFIGURATION,
        title="Test Observation 2",
        fingerprint="fp124"
    )
    obs3 = ObservationService.create_or_get_observation(db_session, obs_in2, setup_data["admin1"])
    assert obs1.id != obs3.id

def test_evidence_storage(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    content = "test evidence content"
    ev1 = EvidenceService.store_evidence(db_session, org_id, EvidenceType.RESPONSE, content)
    ev2 = EvidenceService.store_evidence(db_session, org_id, EvidenceType.RESPONSE, content)

    assert ev1.id == ev2.id
    assert ev1.content_hash == ev2.content_hash

def test_finding_lifecycle_transitions(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["admin1"]

    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="find.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    obs_in = ObservationCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_type=ObservationType.REFLECTED_INPUT,
        title="Test",
        fingerprint="fp111"
    )
    obs = ObservationService.create_or_get_observation(db_session, obs_in, user)

    finding_in = FindingCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_id=obs.id,
        title="Potential XSS",
        status=FindingStatus.POTENTIAL,
        severity=Severity.HIGH
    )
    
    finding = FindingService.create_finding(db_session, finding_in, user)
    assert finding.status == FindingStatus.POTENTIAL

    # Test allowed transition
    FindingService.update_finding_status(db_session, org_id, finding.id, FindingStatus.VERIFIED, user)
    db_session.refresh(finding)
    assert finding.status == FindingStatus.VERIFIED

    # Test invalid transition (VERIFIED to POTENTIAL is not allowed)
    with pytest.raises(ValueError, match="Invalid transition"):
        FindingService.update_finding_status(db_session, org_id, finding.id, FindingStatus.POTENTIAL, user)

@pytest.mark.asyncio
async def test_tenant_isolation_api(client: AsyncClient, setup_data: dict, db_session: Session):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["admin1"]

    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="findAPI.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    obs_in = ObservationCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_type=ObservationType.REFLECTED_INPUT,
        title="Test",
        fingerprint="fpAPI"
    )
    obs = ObservationService.create_or_get_observation(db_session, obs_in, user)

    finding_in = FindingCreate(
        org_id=org_id,
        project_id=project_id,
        asset_id=asset.id,
        observation_id=obs.id,
        title="Potential XSS API",
        status=FindingStatus.POTENTIAL,
        severity=Severity.HIGH
    )
    
    finding = FindingService.create_finding(db_session, finding_in, user)

    # Org2 trying to access finding should 404
    token2 = await get_token(client, "owner2@test.com", "password123")
    resp = await client.get(f"{settings.API_V1_STR}/findings/{finding.id}", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 404

def test_confidence_and_verification_framework(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="conf.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    
    obs_in = ObservationCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_type=ObservationType.SERVER_ERROR, title="Error", fingerprint="fp_conf")
    obs = ObservationService.create_or_get_observation(db_session, obs_in, setup_data["admin1"])
    
    finding_in = FindingCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_id=obs.id, title="Test", status=FindingStatus.POTENTIAL, severity=Severity.MEDIUM)
    finding = FindingService.create_finding(db_session, finding_in, setup_data["admin1"])
    
    conf_in = ConfidenceScoreCreate(org_id=org_id, finding_id=finding.id, level=ConfidenceLevel.HIGH, score_numerical=0.8, reasoning="Test reason")
    score = ConfidenceService.add_confidence_score(db_session, conf_in)
    
    effective = ConfidenceService.get_effective_confidence(db_session, org_id, finding.id)
    assert effective.level == ConfidenceLevel.HIGH
    assert effective.score_numerical == 0.8

def test_audit_logging_findings(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["admin1"]

    from app.models.asset import Asset, AssetType, AssetStatus
    asset = Asset(org_id=org_id, project_id=project_id, name="audit.com", asset_type=AssetType.DOMAIN, status=AssetStatus.VERIFIED)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    
    obs_in = ObservationCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_type=ObservationType.REFLECTED_INPUT, title="Test", fingerprint="fpaudit")
    obs = ObservationService.create_or_get_observation(db_session, obs_in, user)
    
    finding_in = FindingCreate(org_id=org_id, project_id=project_id, asset_id=asset.id, observation_id=obs.id, title="Test Finding", status=FindingStatus.POTENTIAL, severity=Severity.LOW)
    finding = FindingService.create_finding(db_session, finding_in, user)
    
    FindingService.update_finding_status(db_session, org_id, finding.id, FindingStatus.VERIFIED, user)
    
    from app.models.audit_log import AuditLog
    logs = db_session.query(AuditLog).filter(AuditLog.resource_id == str(finding.id)).order_by(AuditLog.created_at.asc()).all()
    assert len(logs) == 2
    assert logs[0].action == "finding.created"
    assert logs[1].action == "finding.status_changed"
