from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.repositories.project import project as crud_project
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("/", response_model=List[Project])
def list_projects(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    List projects for current organization.
    """
    projects = crud_project.get_multi_by_org(db=db, org_id=current_user.org_id, skip=skip, limit=limit)
    return projects

@router.post("/", response_model=Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Create new project.
    Must be admin or owner.
    """
    try:
        project = crud_project.create_with_org(
            db=db, obj_in=project_in, org_id=current_user.org_id, commit=False
        )
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="project.create",
            resource_type="project",
            resource_id=str(project.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        db.rollback()
        raise

@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get project by ID.
    Must belong to user's organization.
    """
    project = crud_project.get_by_org_and_id(db=db, org_id=current_user.org_id, id=project_id)
    if not project:
        raise ResourceNotFoundException(detail="Project not found")
    return project

@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: uuid.UUID,
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Update project.
    Must be admin or owner.
    """
    project = crud_project.get_by_org_and_id(db=db, org_id=current_user.org_id, id=project_id)
    if not project:
        raise ResourceNotFoundException(detail="Project not found")
        
    try:
        project = crud_project.update(db=db, db_obj=project, obj_in=project_in, commit=False)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="project.update",
            resource_type="project",
            resource_id=str(project.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        db.rollback()
        raise

@router.delete("/{project_id}", response_model=Project)
def archive_project(
    project_id: uuid.UUID,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Archive a project.
    Must be admin or owner.
    """
    project = crud_project.get_by_org_and_id(db=db, org_id=current_user.org_id, id=project_id)
    if not project:
        raise ResourceNotFoundException(detail="Project not found")
        
    try:
        project = crud_project.update(db=db, db_obj=project, obj_in={"is_archived": True}, commit=False)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="project.archive",
            resource_type="project",
            resource_id=str(project.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        db.rollback()
        raise
