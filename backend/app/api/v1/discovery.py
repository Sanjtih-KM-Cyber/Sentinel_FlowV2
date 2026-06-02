import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Query, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.discovery import DiscoveryJob, DiscoveryJobCreate, DiscoveredAsset
from app.repositories.asset import asset as crud_asset
from app.repositories.discovery import discovery_job as crud_discovery_job, discovered_asset as crud_discovered_asset
from app.services.audit_service import log_audit_event
from app.services.discovery_pipeline import DiscoveryPipeline
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException

from app.models.discovery_job import DiscoveryStatus

router = APIRouter()

@router.post("/assets/{asset_id}/discover", response_model=DiscoveryJob)
async def start_discovery(
    *,
    db: Session = Depends(get_db),
    asset_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_admin),
    request: Request
) -> Any:
    """
    Start a discovery job for an asset.
    """
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")

    from app.models.discovery_job import DiscoveryJob as DiscoveryJobModel
    existing_job = db.query(DiscoveryJobModel).filter(
        DiscoveryJobModel.asset_id == asset_id,
        DiscoveryJobModel.status.in_([DiscoveryStatus.PENDING, DiscoveryStatus.RUNNING])
    ).first()
    if existing_job:
        raise HTTPException(status_code=409, detail="A discovery job is already running for this asset")

    try:
        job = crud_discovery_job.create_job(
            db=db, 
            obj_in=DiscoveryJobCreate(
                org_id=current_user.org_id,
                project_id=asset_obj.project_id,
                asset_id=asset_obj.id
            ),
            commit=False
        )
        
        log_audit_event(
            db=db,
            org_id=current_user.org_id,
            user=current_user,
            action="discovery.started",
            resource_type="asset",
            resource_id=str(asset_obj.id),
            request=request,
            commit=False
        )
        db.commit()
        db.refresh(job)
        
        # We start the background task, in production this should be a Celery task.
        background_tasks.add_task(DiscoveryPipeline.execute_discovery, db, job, asset_obj)
        
        return job
    except Exception:
        db.rollback()
        raise

@router.get("/assets/{asset_id}/discoveries", response_model=List[DiscoveryJob])
def get_asset_discoveries(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Get all discovery jobs for an asset.
    """
    asset_obj = crud_asset.get_by_org_and_id(db=db, org_id=current_user.org_id, id=asset_id)
    if not asset_obj:
        raise ResourceNotFoundException(detail="Asset not found")
        
    jobs = crud_discovery_job.get_by_org_and_asset(db=db, org_id=current_user.org_id, asset_id=asset_id)
    return jobs

@router.get("/discoveries/{job_id}", response_model=DiscoveryJob)
def get_discovery_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Get discovery job details by ID.
    """
    job = crud_discovery_job.get_by_org_and_id(db=db, org_id=current_user.org_id, id=job_id)
    if not job:
        raise ResourceNotFoundException(detail="Discovery job not found")
        
    return job

@router.get("/discoveries/{job_id}/assets", response_model=List[DiscoveredAsset])
def get_discovered_assets_for_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Get all assets discovered during a specific job.
    """
    job = crud_discovery_job.get_by_org_and_id(db=db, org_id=current_user.org_id, id=job_id)
    if not job:
        raise ResourceNotFoundException(detail="Discovery job not found")
        
    assets = crud_discovered_asset.get_by_job(db=db, job_id=job.id)
    return assets
