import pytest
from tests.fixtures import setup_data, get_token
from app.core.config import settings

@pytest.mark.asyncio
async def test_login_success(client, setup_data):
    token = await get_token(client, "owner1@test.com", "password123")
    assert token is not None

@pytest.mark.asyncio
async def test_login_failure(client, setup_data):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data={"username": "owner1@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"
