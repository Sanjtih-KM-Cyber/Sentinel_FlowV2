import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.asset_verification import VerificationMethod

class AssetVerificationBase(BaseModel):
    method: VerificationMethod

class AssetVerificationCreate(AssetVerificationBase):
    pass

class AssetVerificationInDBBase(AssetVerificationBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    verification_token: str
    created_at: datetime
    last_verified_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AssetVerification(AssetVerificationInDBBase):
    pass
