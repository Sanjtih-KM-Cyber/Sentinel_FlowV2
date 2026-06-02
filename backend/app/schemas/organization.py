import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class WorkspaceType(str, Enum):
    SOLO = "SOLO"
    AGENCY = "AGENCY"
    ENTERPRISE = "ENTERPRISE"

class OrganizationBase(BaseModel):
    name: str
    workspace_type: Optional[WorkspaceType] = WorkspaceType.SOLO
    plan: Optional[str] = "starter"
    sso_enabled: Optional[bool] = False

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    workspace_type: Optional[WorkspaceType] = None
    plan: Optional[str] = None
    sso_enabled: Optional[bool] = None

class OrganizationInDBBase(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Organization(OrganizationInDBBase):
    pass

