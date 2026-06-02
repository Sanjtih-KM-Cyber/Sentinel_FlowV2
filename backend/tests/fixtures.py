import pytest
import uuid
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.core.security import get_password_hash
from app.core.config import settings
from typing import Dict, Any

@pytest.fixture
def setup_data(db_session):
    # Org 1 - Primary Test Org
    org1 = Organization(id=uuid.uuid4(), name="Test Org 1", plan="starter")
    db_session.add(org1)
    
    # Org 2 - For Tenant Isolation Testing
    org2 = Organization(id=uuid.uuid4(), name="Test Org 2", plan="pro")
    db_session.add(org2)
    
    db_session.commit()
    db_session.refresh(org1)
    db_session.refresh(org2)
    
    # Users for Org 1
    owner1 = User(id=uuid.uuid4(), email="owner1@test.com", hashed_password=get_password_hash("password123"), role=UserRole.OWNER, org_id=org1.id)
    admin1 = User(id=uuid.uuid4(), email="admin1@test.com", hashed_password=get_password_hash("password123"), role=UserRole.ADMIN, org_id=org1.id)
    member1 = User(id=uuid.uuid4(), email="member1@test.com", hashed_password=get_password_hash("password123"), role=UserRole.MEMBER, org_id=org1.id)
    
    # Users for Org 2
    owner2 = User(id=uuid.uuid4(), email="owner2@test.com", hashed_password=get_password_hash("password123"), role=UserRole.OWNER, org_id=org2.id)
    
    db_session.add_all([owner1, admin1, member1, owner2])
    db_session.commit()
    
    # Projects
    project1 = Project(id=uuid.uuid4(), name="Project 1", org_id=org1.id)
    project_org2 = Project(id=uuid.uuid4(), name="Project Org 2", org_id=org2.id)
    db_session.add_all([project1, project_org2])
    db_session.commit()
    
    return {
        "org1": org1,
        "org2": org2,
        "owner1": owner1,
        "admin1": admin1,
        "member1": member1,
        "owner2": owner2,
        "project1": project1,
        "project_org2": project_org2
    }

async def get_token(client, email: str, password: str) -> str:
    response = await client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
