import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class AuditLogCreate(BaseModel):
    org_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogInDBBase(AuditLogCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLog(AuditLogInDBBase):
    pass
