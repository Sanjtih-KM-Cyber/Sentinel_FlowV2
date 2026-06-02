from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.organization import Organization, OrganizationUpdate
from app.repositories.organization import organization as crud_org
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("/current", response_model=Organization)
def get_current_organization(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current organization details.
    """
    org = crud_org.get_active(db=db, id=current_user.org_id)
    if not org:
        raise ResourceNotFoundException(detail="Organization not found")
    return org

@router.patch("/current", response_model=Organization)
def update_current_organization(
    *,
    db: Session = Depends(deps.get_db),
    org_in: OrganizationUpdate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Update current organization workspace type and other details.
    Must be an admin or owner.
    """
    org = crud_org.get_active(db=db, id=current_user.org_id)
    if not org:
        raise ResourceNotFoundException(detail="Organization not found")
        
    try:
        org = crud_org.update(db=db, db_obj=org, obj_in=org_in, commit=False)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="organization.update",
            resource_type="organization",
            resource_id=str(current_user.org_id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(org)
        return org
    except Exception as e:
        db.rollback()
        raise

@router.get("/{org_id}", response_model=Organization)
def get_organization(
    org_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get organization details.
    Must be a member of the organization.
    """
    if current_user.org_id != org_id:
        raise PermissionDeniedException(detail="Cannot access this organization")
        
    org = crud_org.get_active(db=db, id=org_id)
    if not org:
        raise ResourceNotFoundException(detail="Organization not found")
    return org

@router.put("/{org_id}", response_model=Organization)
def update_organization(
    org_id: uuid.UUID,
    *,
    db: Session = Depends(deps.get_db),
    org_in: OrganizationUpdate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Update an organization.
    Must be an admin or owner of the organization.
    """
    if current_user.org_id != org_id:
        raise PermissionDeniedException(detail="Cannot access this organization")
        
    org = crud_org.get_active(db=db, id=org_id)
    if not org:
        raise ResourceNotFoundException(detail="Organization not found")
        
    try:
        org = crud_org.update(db=db, db_obj=org, obj_in=org_in, commit=False)
        
        log_audit_event(
            db=db,
            org_id=org_id,
            user=current_user,
            action="organization.update",
            resource_type="organization",
            resource_id=str(org_id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(org)
        return org
    except Exception as e:
        db.rollback()
        raise

@router.delete("/{org_id}", response_model=Organization)
def delete_organization(
    org_id: uuid.UUID,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
    request: Request
) -> Any:
    """
    Soft delete an organization.
    Must be the owner.
    """
    if current_user.org_id != org_id:
        raise PermissionDeniedException(detail="Cannot access this organization")
        
    org = crud_org.get_active(db=db, id=org_id)
    if not org:
        raise ResourceNotFoundException(detail="Organization not found")
        
    # Soft delete
    try:
        org = crud_org.update(db=db, db_obj=org, obj_in={"is_deleted": True}, commit=False)
        
        log_audit_event(
            db=db,
            org_id=org_id,
            user=current_user,
            action="organization.delete",
            resource_type="organization",
            resource_id=str(org_id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(org)
        return org
    except Exception as e:
        db.rollback()
        raise
