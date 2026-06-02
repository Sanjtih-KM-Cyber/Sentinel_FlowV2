import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.observation_finding import Observation, Evidence, Finding, FindingUpdate, FindingStatus
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.finding_service import FindingService
from app.core.exceptions import ResourceNotFoundException

router = APIRouter()

# Observations
@router.get("/observations", response_model=List[Observation])
def get_observations(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    return ObservationService.get_observations(db, current_user.org_id)

@router.get("/observations/{id}", response_model=Observation)
def get_observation(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    obs = ObservationService.get_observation(db, current_user.org_id, id)
    if not obs:
        raise ResourceNotFoundException(detail="Observation not found")
    return obs

# Evidence
@router.get("/evidence", response_model=List[Evidence])
def get_evidence(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    return EvidenceService.get_all_evidence(db, current_user.org_id)

@router.get("/evidence/{id}", response_model=Evidence)
def get_evidence_by_id(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    ev = EvidenceService.get_evidence(db, current_user.org_id, id)
    if not ev:
        raise ResourceNotFoundException(detail="Evidence not found")
    return ev

# Findings
@router.get("/findings", response_model=List[Finding])
def get_findings(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    return FindingService.get_findings(db, current_user.org_id)

@router.get("/findings/{id}", response_model=Finding)
def get_finding_by_id(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    f = FindingService.get_finding(db, current_user.org_id, id)
    if not f:
        raise ResourceNotFoundException(detail="Finding not found")
    return f

@router.patch("/findings/{id}/status", response_model=Finding)
def update_finding_status(
    id: uuid.UUID,
    status_update: FindingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    if not status_update.status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    try:
        f = FindingService.update_finding_status(
            db=db, 
            org_id=current_user.org_id, 
            finding_id=id, 
            new_status=status_update.status,
            user=current_user,
            request=request
        )
        return f
    except ValueError as e:
        if str(e) == "Finding not found":
            raise ResourceNotFoundException(detail="Finding not found")
        raise HTTPException(status_code=400, detail=str(e))
