from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate
from app.repositories.base import CRUDBase

class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    def create_with_org_project(
        self, db: Session, *, obj_in: AssetCreate, org_id: uuid.UUID, commit: bool = True
    ) -> Asset:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, org_id=org_id)
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

    def get_multi_by_org_project(
        self, db: Session, *, org_id: uuid.UUID, project_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Asset]:
        query = db.query(self.model).filter(Asset.org_id == org_id, Asset.is_archived == False)
        if project_id:
            query = query.filter(Asset.project_id == project_id)
        return query.offset(skip).limit(limit).all()
        
    def get_by_org_and_id(
        self, db: Session, *, org_id: uuid.UUID, id: uuid.UUID
    ) -> Optional[Asset]:
        return db.query(self.model).filter(Asset.org_id == org_id, Asset.id == id, Asset.is_archived == False).first()

asset = CRUDAsset(Asset)
