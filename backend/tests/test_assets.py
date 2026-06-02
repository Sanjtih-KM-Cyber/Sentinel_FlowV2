import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.orm import Session
from app.core.config import settings
from tests.fixtures import setup_data, get_token
from app.models.asset import AssetStatus
from app.models.audit_log import AuditLog
from app.models.asset_verification import VerificationMethod

@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient, setup_data: dict, db_session: Session):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "example.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "example.com"
    assert data["status"] == "pending_verification"
    assert data["asset_type"] == "domain"
    
    # Audit log check
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "asset.create",
        AuditLog.resource_id == data["id"]
    ).first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_create_duplicate_asset(client: AsyncClient, setup_data: dict, db_session: Session):
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # First creation should succeed
    response1 = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "duplicate.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    assert response1.status_code == 200
    
    # Second creation should fail
    response2 = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "duplicate.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    assert response2.status_code == 500 or response2.status_code == 400 or response2.status_code == 409

@pytest.mark.asyncio
async def test_tenant_isolation_create_asset(client: AsyncClient, setup_data: dict, db_session: Session):
    org2 = setup_data["org2"]
    project2 = setup_data["project_org2"]
    token = await get_token(client, "admin1@test.com", "password123") # Belongs to org1
    
    response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "attacker.com",
            "asset_type": "domain",
            "project_id": str(project2.id) # Try to create in org2's project
        }
    )
    
    assert response.status_code == 404 # Resource not found because they can't access project2

@pytest.mark.asyncio
async def test_request_verification(client: AsyncClient, setup_data: dict, db_session: Session):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    create_response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "verify_me.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    asset_id = create_response.json()["id"]
    
    # Request verification
    verify_response = await client.post(
        f"{settings.API_V1_STR}/assets/{asset_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "method": "dns_txt"
        }
    )
    
    assert verify_response.status_code == 200
    data = verify_response.json()
    assert data["method"] == "dns_txt"
    assert "verification_token" in data
    
    # Status should be failed or verified (in our test it will fail without patching dnspython)
    asset_response = await client.get(
        f"{settings.API_V1_STR}/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert asset_response.json()["status"] == "verification_failed"

@pytest.mark.asyncio
async def test_archive_asset(client: AsyncClient, setup_data: dict, db_session: Session):
    org = setup_data["org1"]
    project = setup_data["project1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    create_response = await client.post(
        f"{settings.API_V1_STR}/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "archive_me.com",
            "asset_type": "domain",
            "project_id": str(project.id)
        }
    )
    asset_id = create_response.json()["id"]
    
    archive_response = await client.delete(
        f"{settings.API_V1_STR}/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True
    assert archive_response.json()["status"] == "archived"
    
    # Verify we can't get it anymore
    get_response = await client.get(
        f"{settings.API_V1_STR}/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404
