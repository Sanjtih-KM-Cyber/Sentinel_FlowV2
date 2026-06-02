from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.models.asset_verification import AssetVerification
from app.schemas.asset_verification import AssetVerificationCreate
from app.repositories.base import CRUDBase

class CRUDAssetVerification(CRUDBase[AssetVerification, AssetVerificationCreate, AssetVerificationCreate]):
    def get_by_asset(
        self, db: Session, *, asset_id: uuid.UUID
    ) -> List[AssetVerification]:
        return db.query(self.model).filter(AssetVerification.asset_id == asset_id).all()
        
    def get_active_by_asset_method(
        self, db: Session, *, asset_id: uuid.UUID, method: str
    ) -> Optional[AssetVerification]:
        return db.query(self.model).filter(AssetVerification.asset_id == asset_id, AssetVerification.method == method).first()

asset_verification = CRUDAssetVerification(AssetVerification)
