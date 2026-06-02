import pytest
from app.schemas.organization import OrganizationUpdate, WorkspaceType
from app.repositories.organization import organization as crud_org
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_trace(client: TestClient, setup_data):
    # This test will literally print out everything we need
    # We will run pytest with -s so prints go to stdout
    org = setup_data["org1"]
    
    # 1. Login
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "owner1@test.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- TRACE START ---")
    
    # GET
    res = client.get(f"{settings.API_V1_STR}/organizations/current", headers=headers)
    print("1. GET /organizations/current response payload:")
    print(res.json())
    
    # PATCH
    payload = {"workspace_type": "AGENCY"}
    print(f"\n2. PATCH /organizations/current sending payload: {payload}")
    res = client.patch(
        f"{settings.API_V1_STR}/organizations/current", 
        headers=headers,
        json=payload
    )
    print("3. PATCH response payload:")
    patch_res = res.json()
    print(patch_res)
    
    # GET again
    res = client.get(f"{settings.API_V1_STR}/organizations/current", headers=headers)
    print("\n4. GET /organizations/current response payload after patch:")
    print(res.json())

    # Check DB via raw query
    from app.api.deps import get_db
    db = next(get_db())
    raw = db.execute(f"SELECT workspace_type FROM organizations WHERE id = '{org.id}'")
    val = raw.scalar()
    print(f"\n5. Database SELECT workspace_type FROM organizations: {val}")
    
    print("--- TRACE END ---")
