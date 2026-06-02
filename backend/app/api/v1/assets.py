import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.asset import AssetStatus
from app.schemas.asset import Asset, AssetCreate, AssetUpdate
from app.schemas.asset_verification import AssetVerificationCreate, AssetVerification
from app.repositories.asset import asset as crud_asset
from app.repositories.asset_verification import asset_verification as crud_asset_verification
from app.services.audit_service import log_audit_event
from app.services.verification_service import VerificationService
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException

router = APIRouter()

@router.post("/", response_model=Asset)
async def create_asset(
    *,
    db: Session = Depends(get_db),
    asset_in: AssetCreate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    # We must ensure project belongs to the user's organization
    from app.repositories.project import project as crud_project
    project = crud_project.get(db, id=asset_in.project_id)
    if not project or project.org_id != current_user.org_id:
        raise ResourceNotFoundException(detail="Project not found")

    try:
        new_asset = crud_asset.create_with_org_project(
            db=db, obj_in=asset_in, org_id=current_user.org_id, commit=False
        )
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="asset.create",
            resource_type="asset",
            resource_id=str(new_asset.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(new_asset)
        return new_asset
    except Exception as e:
        db.rollback()
        if "uq_asset_org_name" in str(e):
            raise HTTPException(status_code=400, detail="Asset with this name already exists in the organization")
        raise

@router.get("/", response_model=List[Asset])
def read_assets(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    project_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    assets = crud_asset.get_multi_by_org_project(
        db=db, org_id=current_user.org_id, project_id=project_id, skip=skip, limit=limit
    )
    return assets

@router.get("/{asset_id}", response_model=Asset)
def get_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")
    return asset_obj

@router.patch("/{asset_id}", response_model=Asset)
def update_asset(
    *,
    db: Session = Depends(get_db),
    asset_id: uuid.UUID,
    asset_in: AssetUpdate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")

    try:
        asset_obj = crud_asset.update(db=db, db_obj=asset_obj, obj_in=asset_in, commit=False)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="asset.update",
            resource_type="asset",
            resource_id=str(asset_obj.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(asset_obj)
        return asset_obj
    except Exception as e:
        db.rollback()
        if "uq_asset_org_name" in str(e):
            raise HTTPException(status_code=400, detail="Asset with this name already exists in the organization")
        raise

@router.delete("/{asset_id}", response_model=Asset)
def archive_asset(
    *,
    db: Session = Depends(get_db),
    asset_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")

    try:
        asset_obj = crud_asset.update(db=db, db_obj=asset_obj, obj_in={"is_archived": True, "status": AssetStatus.ARCHIVED}, commit=False)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="asset.archive",
            resource_type="asset",
            resource_id=str(asset_obj.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(asset_obj)
        return asset_obj
    except Exception:
        db.rollback()
        raise

@router.post("/{asset_id}/verify", response_model=AssetVerification)
async def generate_or_run_verification(
    *,
    db: Session = Depends(get_db),
    asset_id: uuid.UUID,
    verification_in: AssetVerificationCreate,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")

    # Determine if we already have a token for this method
    verification = crud_asset_verification.get_active_by_asset_method(
        db=db, asset_id=asset_obj.id, method=verification_in.method
    )
    
    try:
        if not verification:
            token = VerificationService.generate_verification_token()
            verification = crud_asset_verification.create(
                db=db,
                obj_in={"asset_id": asset_obj.id, "method": verification_in.method, "verification_token": token},
                commit=False
            )
            verification.asset_id = asset_obj.id
            db.add(verification)
            db.flush()
            
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="asset.verify.requested",
            resource_type="asset",
            resource_id=str(asset_obj.id),
            request=request,
            commit=False
        )
        # Execute verification
        is_verified, error_msg = await VerificationService.run_verification(db, asset_obj, verification)
        
        verification.last_verified_at = datetime.utcnow()
        if is_verified:
            asset_obj.status = AssetStatus.VERIFIED
            verification.error_message = None
            log_action = "asset.verify.succeeded"
        else:
            asset_obj.status = AssetStatus.VERIFICATION_FAILED
            verification.error_message = error_msg or "Verification failed"
            log_action = "asset.verify.failed"

        db.add(verification)
        db.add(asset_obj)
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action=log_action,
            resource_type="asset",
            resource_id=str(asset_obj.id),
            request=request,
            commit=False
        )

        db.commit()
        db.refresh(verification)
        return verification
    except Exception:
        db.rollback()
        raise

@router.get("/{asset_id}/verification", response_model=List[AssetVerification])
def get_asset_verifications(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")
        
    return crud_asset_verification.get_by_asset(db=db, asset_id=asset_obj.id)
