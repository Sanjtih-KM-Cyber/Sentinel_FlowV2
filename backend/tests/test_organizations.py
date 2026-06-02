import pytest
from tests.fixtures import setup_data, get_token
from app.core.config import settings
import uuid

@pytest.mark.asyncio
async def test_get_current_organization(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    response = await client.get(
        f"{settings.API_V1_STR}/organizations/current",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(org.id)
    assert "workspace_type" in response.json()
    assert response.json()["workspace_type"] == "SOLO"

@pytest.mark.asyncio
async def test_update_current_organization_workspace_type(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    response = await client.patch(
        f"{settings.API_V1_STR}/organizations/current",
        headers={"Authorization": f"Bearer {token}"},
        json={"workspace_type": "ENTERPRISE"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(org.id)
    assert response.json()["workspace_type"] == "ENTERPRISE"
    
    # Verify persistence
    response = await client.get(
        f"{settings.API_V1_STR}/organizations/current",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["workspace_type"] == "ENTERPRISE"

@pytest.mark.asyncio
async def test_get_organization_owner(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    response = await client.get(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(org.id)

@pytest.mark.asyncio
async def test_tenant_isolation_org(client, setup_data):
    org2 = setup_data["org2"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    response = await client.get(
        f"{settings.API_V1_STR}/organizations/{org2.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_organization_admin(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.put(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Org Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Org Name"

@pytest.mark.asyncio
async def test_update_organization_member_forbidden(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "member1@test.com", "password123")
    
    response = await client.put(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Org Name"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_organization_owner(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    response = await client.delete(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Verify it's gone
    response = await client.get(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_organization_admin_forbidden(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.delete(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
