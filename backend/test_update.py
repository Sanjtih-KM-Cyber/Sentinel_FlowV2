from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid

class WorkspaceType(str, Enum):
    SOLO = "SOLO"
    AGENCY = "AGENCY"
    ENTERPRISE = "ENTERPRISE"

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    workspace_type: Optional[WorkspaceType] = None
    plan: Optional[str] = None
    sso_enabled: Optional[bool] = None

class MockSQLAModel:
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = "Test"
        self.workspace_type = WorkspaceType.SOLO
        # sqlalchemy puts this
        self._sa_instance_state = "something"

from fastapi.encoders import jsonable_encoder

db_obj = MockSQLAModel()
obj_data = jsonable_encoder(db_obj)
print("obj_data:", obj_data)

obj_in = OrganizationUpdate(workspace_type=WorkspaceType.AGENCY)
update_data = obj_in.model_dump(exclude_unset=True)
print("update_data:", update_data)

for field in obj_data:
    if field in update_data:
        setattr(db_obj, field, update_data[field])

print("db_obj.workspace_type:", db_obj.workspace_type)
