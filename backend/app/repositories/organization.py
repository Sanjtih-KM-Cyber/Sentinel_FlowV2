from typing import Optional
import uuid
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.repositories.base import CRUDBase

class CRUDOrganization(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
    def get_active(self, db: Session, id: uuid.UUID) -> Optional[Organization]:
        return db.query(self.model).filter(Organization.id == id, Organization.is_deleted == False).first()

organization = CRUDOrganization(Organization)
