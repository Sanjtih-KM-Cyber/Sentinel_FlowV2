from typing import Optional
import uuid
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.repositories.base import CRUDBase

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_org(
        self, db: Session, *, obj_in: ProjectCreate, org_id: uuid.UUID, commit: bool = True
    ) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, org_id=org_id)
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

    def get_multi_by_org(
        self, db: Session, *, org_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[Project]:
        return (
            db.query(self.model)
            .filter(Project.org_id == org_id, Project.is_archived == False)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_by_org_and_id(
        self, db: Session, *, org_id: uuid.UUID, id: uuid.UUID
    ) -> Optional[Project]:
        return db.query(self.model).filter(Project.org_id == org_id, Project.id == id, Project.is_archived == False).first()

project = CRUDProject(Project)
