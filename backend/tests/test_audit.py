import pytest
from tests.fixtures import setup_data, get_token
from app.core.config import settings
from app.models.audit_log import AuditLog

@pytest.mark.asyncio
async def test_audit_log_login(client, setup_data, db_session):
    org = setup_data["org1"]
    
    # Login should create an audit log
    token = await get_token(client, "owner1@test.com", "password123")
    
    # Check DB
    audit_log = db_session.query(AuditLog).filter(AuditLog.action == "user.login").first()
    assert audit_log is not None
    assert str(audit_log.org_id) == str(org.id)

@pytest.mark.asyncio
async def test_audit_log_org_update(client, setup_data, db_session):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.put(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Org Update Auth Test"}
    )
    assert response.status_code == 200
    
    # Check DB
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "organization.update", 
        AuditLog.resource_id == str(org.id)
    ).first()
    assert audit_log is not None
    assert str(audit_log.user_id) == str(setup_data["admin1"].id)
    assert audit_log.resource_type == "organization"

@pytest.mark.asyncio
async def test_audit_log_project_create(client, setup_data, db_session):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Audit Test Project", "description": "Desc"}
    )
    assert response.status_code == 200
    proj_id = response.json()["id"]
    
    # Check DB
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "project.create", 
        AuditLog.resource_id == proj_id
    ).first()
    assert audit_log is not None
    assert str(audit_log.org_id) == str(org.id)
    assert str(audit_log.user_id) == str(setup_data["admin1"].id)
    assert audit_log.resource_type == "project"

@pytest.mark.asyncio
async def test_audit_log_project_update(client, setup_data, db_session):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create project first
    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Audit Test Project 2", "description": "Desc"}
    )
    proj_id = response.json()["id"]
    
    # Update project
    update_response = await client.put(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Audit Test Project"}
    )
    
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "project.update", 
        AuditLog.resource_id == proj_id
    ).first()
    assert audit_log is not None
    assert str(audit_log.org_id) == str(org.id)
    assert str(audit_log.user_id) == str(setup_data["admin1"].id)
    assert audit_log.resource_type == "project"

@pytest.mark.asyncio
async def test_audit_log_project_archive(client, setup_data, db_session):
    org = setup_data["org1"]
    token = await get_token(client, "admin1@test.com", "password123")
    
    # Create project first
    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Audit Test Project 3"}
    )
    proj_id = response.json()["id"]
    
    # Archive project
    archive_response = await client.delete(
        f"{settings.API_V1_STR}/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "project.archive", 
        AuditLog.resource_id == proj_id
    ).first()
    assert audit_log is not None
    assert str(audit_log.org_id) == str(org.id)
    assert str(audit_log.user_id) == str(setup_data["admin1"].id)
    assert audit_log.resource_type == "project"

@pytest.mark.asyncio
async def test_soft_deleted_org_enforcement_and_audit(client, setup_data, db_session):
    org = setup_data["org1"]
    token = await get_token(client, "owner1@test.com", "password123")
    
    # Delete org
    response = await client.delete(
        f"{settings.API_V1_STR}/organizations/{org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Check org delete audit log
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "organization.delete", 
        AuditLog.resource_id == str(org.id)
    ).first()
    assert audit_log is not None
    assert str(audit_log.org_id) == str(org.id)
    assert str(audit_log.user_id) == str(setup_data["owner1"].id)
    assert audit_log.resource_type == "organization"
    
    # Now try to access an endpoint with the valid token -> should be 403 because org is deleted
    response2 = await client.get(
        f"{settings.API_V1_STR}/projects/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 403
    assert response2.json()["detail"] == "Organization is deleted"
