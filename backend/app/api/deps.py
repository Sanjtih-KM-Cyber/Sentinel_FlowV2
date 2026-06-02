from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core import security, exceptions
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise exceptions.InvalidCredentialsException()
    
    # We should query using the repository pattern, but for brevity using db query
    user = db.query(User).options(joinedload(User.organization)).filter(User.id == token_data.sub).first()
    if not user:
        raise exceptions.ResourceNotFoundException(detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if user.organization and user.organization.is_deleted:
        raise exceptions.PermissionDeniedException(detail="Organization is deleted")
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise exceptions.PermissionDeniedException(detail="The user doesn't have enough privileges")
    return current_user

def get_current_active_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.OWNER:
        raise exceptions.PermissionDeniedException(detail="Must be organization owner")
    return current_user
