import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.asset import AssetType, AssetStatus

class AssetBase(BaseModel):
    name: str
    asset_type: AssetType
    project_id: uuid.UUID

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[AssetStatus] = None

class AssetInDBBase(AssetBase):
    id: uuid.UUID
    org_id: uuid.UUID
    status: AssetStatus
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Asset(AssetInDBBase):
    pass
