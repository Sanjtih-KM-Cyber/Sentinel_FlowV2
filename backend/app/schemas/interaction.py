from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class InteractionTokenCreate(BaseModel):
    org_id: uuid.UUID
    project_id: uuid.UUID
    source_module: str

class InteractionTokenResponse(BaseModel):
    id: uuid.UUID
    token: str
    org_id: uuid.UUID
    project_id: uuid.UUID
    source_module: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class InteractionEventCreate(BaseModel):
    token_str: str
    protocol: str
    source_ip: str
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None

class InteractionEventResponse(BaseModel):
    id: uuid.UUID
    token_id: uuid.UUID
    protocol: str
    source_ip: str
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
