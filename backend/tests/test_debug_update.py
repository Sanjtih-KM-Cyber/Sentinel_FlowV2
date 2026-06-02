import pytest
from app.schemas.organization import OrganizationUpdate, WorkspaceType
from app.repositories.organization import organization as crud_org

@pytest.mark.asyncio
async def test_debug_update(db, setup_data):
    org = setup_data["org1"]
    
    # Check current DB state
    assert org.workspace_type == WorkspaceType.SOLO
    
    # Try updating
    org_in = OrganizationUpdate(workspace_type=WorkspaceType.AGENCY)
    updated_org = crud_org.update(db=db, db_obj=org, obj_in=org_in)
    
    # Verify in-memory model
    assert updated_org.workspace_type == WorkspaceType.AGENCY
    
    # Verify DB commit
    db.refresh(org)
    assert org.workspace_type == WorkspaceType.AGENCY
