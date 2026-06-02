from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.interaction_service import InteractionService
from app.schemas.interaction import InteractionTokenCreate, InteractionTokenResponse, InteractionEventResponse

router = APIRouter()

@router.post("/token", response_model=InteractionTokenResponse)
def create_interaction_token(
    token_in: InteractionTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates an out-of-band interaction token associated with a project.
    """
    token = InteractionService.generate_token(db, token_in)
    return token

@router.get("/events", response_model=List[InteractionEventResponse])
def list_interaction_events(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists interaction events for an organization.
    """
    events = InteractionService.get_all_events(db, org_id)
    return events

@router.get("/{token_str}", response_model=List[InteractionEventResponse])
def get_events_for_token(
    token_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists interaction events corresponding to a specific token.
    """
    events = InteractionService.get_events_for_token(db, token_str)
    return events
