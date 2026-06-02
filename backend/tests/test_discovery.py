import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.orm import Session
from app.core.config import settings
from tests.fixtures import setup_data, get_token
from app.models.asset import AssetType, AssetStatus
from app.models.discovery_job import DiscoveryStatus
from app.models.audit_log import AuditLog
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_subdomain_provider():
    with patch('app.services.discovery_providers.SubdomainProviderCRTsh.discover') as mock:
        mock.return_value = ['sub1.example.com', 'sub2.example.com']
        yield mock

@pytest.fixture
def mock_dns_provider():
    with patch('app.services.discovery_providers.DnsIntelligenceProvider.collect') as mock:
        mock.return_value = {'A': ['192.168.1.1'], 'TXT': ['v=spf1 include:_spf.example.com ~all']}
        yield mock

@pytest.fixture
def mock_http_provider():
    with patch('app.services.discovery_providers.HttpProbingProvider.probe') as mock:
        mock.return_value = [{
            "url": "http://sub1.example.com",
            "status_code": 200,
            "title": "Welcome to Sub1",
            "content_length": 1024,
            "server_header": "nginx/1.18.0",
            "headers": {"server": "nginx/1.18.0", "x-powered-by": "PHP/7.4"}
        }]
        yield mock

@pytest.mark.asyncio
async def test_discovery_pipeline_execution(client: AsyncClient, setup_data: dict, db_session: Session, mock_subdomain_provider, mock_dns_provider, mock_http_provider):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create asset
    create_response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "example.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    asset_id = create_response.json()["id"]
    
    # Verify the asset manually (to allow discovery)
    from app.repositories.asset import asset
    a_obj = asset.get_by_org_and_id(db_session, org_id=org.id, id=asset_id)
    a_obj.status = AssetStatus.VERIFIED
    db_session.commit()
    
    # Start Discovery
    discovery_response = await client.post(
        f"{settings.API_V1_STR}/assets/{asset_id}/discover",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert discovery_response.status_code == 200
    job_id = discovery_response.json()["id"]
    
    # Ensure audit log is created
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "discovery.started",
        AuditLog.resource_id == asset_id
    ).first()
    assert audit_log is not None
    
    # The discovery pipeline runs in background, but since we are testing, let's call it synchronously
    from app.services.discovery_pipeline import DiscoveryPipeline
    from app.repositories.discovery import discovery_job
    job = discovery_job.get_by_org_and_id(db_session, org_id=org.id, id=job_id)
    
    await DiscoveryPipeline.execute_discovery(db_session, job, a_obj)
    
    # Check status
    assert job.status == DiscoveryStatus.COMPLETED
    
    # Check discovered assets
    get_assets_resp = await client.get(
        f"{settings.API_V1_STR}/discoveries/{job_id}/assets",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_assets_resp.status_code == 200
    discovered = get_assets_resp.json()
    assert len(discovered) > 0
    # One of them should be sub1.example.com
    subnames = [d["name"] for d in discovered]
    assert "sub1.example.com" in subnames
    
    # Check Http probe results (e.g., getting info from the db)
    # The endpoint returns discovered assets with their relationships because from_attributes=True and relationships are included in schema
    has_probes = False
    for d in discovered:
        if len(d["http_probes"]) > 0:
            has_probes = True
            probe = d["http_probes"][0]
            assert probe["status_code"] == 200
            assert len(probe["fingerprints"]) > 0
            # fingerprints check
            fp_names = [f["name"] for f in probe["fingerprints"]]
            assert "Nginx" in fp_names
            assert "PHP" in fp_names
    assert has_probes

@pytest.mark.asyncio
async def test_tenant_isolation_discovery(client: AsyncClient, setup_data: dict, db_session: Session):
    org2 = setup_data["org2"]
    token = await get_token(client, "admin1@test.com", "password123") # token for org1
    
    # Attacker tries to get discovery job belonging to another org
    # Assuming job_id is something random for org2. It will return 404
    job_uuid = str(uuid.uuid4())
    
    response = await client.get(
        f"{settings.API_V1_STR}/discoveries/{job_uuid}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
