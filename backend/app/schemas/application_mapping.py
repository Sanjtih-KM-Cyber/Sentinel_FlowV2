from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl
import uuid

class ApplicationSessionCreate(BaseModel):
    org_id: uuid.UUID
    project_id: uuid.UUID
    session_type: str
    cookies: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None

class DiscoveredEndpointCreate(BaseModel):
    org_id: uuid.UUID
    project_id: uuid.UUID
    method: str
    url: str
    source: str
    is_api: bool = False
    is_form: bool = False

class DiscoveredParameterCreate(BaseModel):
    endpoint_id: uuid.UUID
    name: str
    param_type: str
    data_type: Optional[str] = None
    is_required: bool = False
    is_hidden: bool = False
    default_value: Optional[str] = None

class DiscoveredObjectCreate(BaseModel):
    org_id: uuid.UUID
    project_id: uuid.UUID
    object_type: str
    identifier: str
    source_endpoint_id: Optional[uuid.UUID] = None
    owner_context: Optional[str] = None
    access_context: Optional[str] = None

class WorkflowStepCreate(BaseModel):
    step_order: int
    endpoint_id: Optional[uuid.UUID] = None
    action_type: str
    payload: Optional[Dict[str, Any]] = None
    expected_state_change: Optional[str] = None

class WorkflowCreate(BaseModel):
    org_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStepCreate] = []
