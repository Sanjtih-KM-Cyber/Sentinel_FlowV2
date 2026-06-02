from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.api import deps
from app.models.user import User
from app.schemas.token import Token
from app.services.audit_service import log_audit_event
from app.api.rate_limit import rate_limit_login

router = APIRouter()

@router.post("/access-token", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    rate_limit_login(request, form_data.username)
    
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    log_audit_event(
        db=db,
        org_id=user.org_id,
        user=user,
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        request=request
    )
    
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
