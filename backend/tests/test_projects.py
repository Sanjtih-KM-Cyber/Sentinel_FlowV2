import pytest
from tests.fixtures import setup_data, get_token
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_project_admin(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Project", "description": "Desc"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Project"
    return response.json()

@pytest.mark.asyncio
async def test_create_project_member_forbidden(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "member1@test.com", "password123")
    
    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Project", "description": "Desc"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_projects_flow(client, setup_data):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create project
    proj_response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Proj 1"}
    )
    proj_id = proj_response.json()["id"]
    
    # Get by ID
    get_response = await client.get(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    
    # List projects
    list_response = await client.get(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) > 0
    
    # Update project
    update_response = await client.put(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Proj"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Proj"
    
    # Archive project
    arc_response = await client.delete(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert arc_response.status_code == 200
    
    # Get by ID (should be 404 since it's archived)
    get_arc_response = await client.get(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_arc_response.status_code == 404

@pytest.mark.asyncio
async def test_tenant_isolation_get_project(client, setup_data):
    org2 = setup_data["org2"]
    token2 = await get_token(client, "owner2@test.com", "password123")
    token1 = await get_token(client, "admin1@test.com", "password123")
    
    proj_response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token2}"},
        json={"name": "Org 2 Proj"}
    )
    proj_id = proj_response.json()["id"]
    
    # Try to access from org1
    get_response = await client.get(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert get_response.status_code == 404 # ResourceNotFound is thrown when get_by_org_and_id fails
