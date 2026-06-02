import pytest
from app.schemas.organization import OrganizationUpdate, WorkspaceType

def test_organization_schema_workspace_type():
    update_data = {"name": "Test", "workspace_type": WorkspaceType.AGENCY}
    schema = OrganizationUpdate(**update_data)
    assert schema.name == "Test"
    assert schema.workspace_type == WorkspaceType.AGENCY

def test_organization_schema_workspace_type_default():
    update_data = {"name": "Test"}
    schema = OrganizationUpdate(**update_data)
    assert schema.name == "Test"
    assert schema.workspace_type is None
