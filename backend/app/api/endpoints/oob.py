from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.interaction import InteractionEventCreate
from app.services.interaction_service import InteractionService

router = APIRouter()

@router.api_route("/{token_str}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def receive_oob_interaction(
    token_str: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for receiving out-of-band callbacks.
    This acts as the HTTP receiver for interaction tokens.
    """
    headers = dict(request.headers)
    body = ""
    try:
        body_bytes = await request.body()
        body = body_bytes.decode()
    except Exception:
        pass
        
    event_in = InteractionEventCreate(
        token_str=token_str,
        protocol="HTTP",
        source_ip=request.client.host if request.client else "unknown",
        request_headers=headers,
        request_body=body
    )
    
    InteractionService.record_event(db, event_in)
    
    return {"status": "ok"}
