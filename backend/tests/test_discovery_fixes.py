import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.orm import Session
from app.core.config import settings
from tests.fixtures import setup_data, get_token
from app.models.asset import AssetType, AssetStatus
from app.models.discovery_job import DiscoveryStatus
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_concurrent_discovery_rejection(client: AsyncClient, setup_data: dict, db_session: Session):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create asset
    create_response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "example-concurrent.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    asset_id = create_response.json()["id"]
    
    # First discovery
    resp1 = await client.post(
        f"{settings.API_V1_STR}/assets/{asset_id}/discover",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == 200
    
    # Second discovery immediately should fail with 409
    resp2 = await client.post(
        f"{settings.API_V1_STR}/assets/{asset_id}/discover",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 409

@pytest.mark.asyncio
async def test_duplicate_discovery_prevention(client: AsyncClient, setup_data: dict, db_session: Session):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create asset
    create_response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "example-dup.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    asset_id = create_response.json()["id"]
    
    from app.repositories.asset import asset
    a_obj = asset.get_by_org_and_id(db_session, org_id=org.id, id=asset_id)
    a_obj.status = AssetStatus.VERIFIED
    db_session.commit()

    with patch('app.services.discovery_providers.SubdomainProviderCRTsh.discover') as mock_sub, \
         patch('app.services.discovery_providers.DnsIntelligenceProvider.collect') as mock_dns, \
         patch('app.services.discovery_providers.HttpProbingProvider.probe') as mock_http:
        
        mock_sub.return_value = ['sub.example-dup.com']
        mock_dns.return_value = {}
        mock_http.return_value = []
        
        # Start Discovery 1
        resp1 = await client.post(
            f"{settings.API_V1_STR}/assets/{asset_id}/discover",
            headers={"Authorization": f"Bearer {token}"}
        )
        job_id1 = resp1.json()["id"]
        
        from app.services.discovery_pipeline import DiscoveryPipeline
        from app.repositories.discovery import discovery_job
        job1 = discovery_job.get_by_org_and_id(db_session, org_id=org.id, id=job_id1)
        await DiscoveryPipeline.execute_discovery(db_session, job1, a_obj)
        
        # We need to manually change status from COMPLETED back to something else or mock it since start_discovery 
        # prevents concurrent runs, but job1 is completed now.
        resp2 = await client.post(
            f"{settings.API_V1_STR}/assets/{asset_id}/discover",
            headers={"Authorization": f"Bearer {token}"}
        )
        job_id2 = resp2.json()["id"]
        job2 = discovery_job.get_by_org_and_id(db_session, org_id=org.id, id=job_id2)
        await DiscoveryPipeline.execute_discovery(db_session, job2, a_obj)
        
        # Check total discovered assets for the parent asset
        from app.models.discovered_asset import DiscoveredAsset
        assets = db_session.query(DiscoveredAsset).filter(DiscoveredAsset.parent_asset_id == asset_id).all()
        # Should be 2: original and the sub domain
        assert len(assets) == 2
        # The latest job id should be job2
        for a in assets:
            assert a.discovery_job_id == job2.id
