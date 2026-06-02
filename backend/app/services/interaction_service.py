import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.interaction import InteractionToken, InteractionEvent
from app.schemas.interaction import InteractionTokenCreate, InteractionEventCreate

class InteractionService:
    @staticmethod
    def generate_token(db: Session, token_in: InteractionTokenCreate) -> InteractionToken:
        # Generate a secure short token (e.g., 16 chars hex)
        raw_token = secrets.token_hex(8)
        
        expires_at = datetime.utcnow() + timedelta(days=7) # arbitrary expiration
        
        db_token = InteractionToken(
            org_id=token_in.org_id,
            project_id=token_in.project_id,
            token=raw_token,
            source_module=token_in.source_module,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    @staticmethod
    def get_token(db: Session, token_str: str) -> InteractionToken:
        return db.query(InteractionToken).filter(InteractionToken.token == token_str).first()

    @staticmethod
    def record_event(db: Session, event_in: InteractionEventCreate) -> InteractionEvent:
        db_token = InteractionService.get_token(db, event_in.token_str)
        if not db_token:
            return None # Ignore invalid tokens
            
        db_event = InteractionEvent(
            token_id=db_token.id,
            protocol=event_in.protocol,
            source_ip=event_in.source_ip,
            request_headers=event_in.request_headers,
            request_body=event_in.request_body
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    @staticmethod
    def get_events_for_token(db: Session, token_str: str) -> list[InteractionEvent]:
        db_token = InteractionService.get_token(db, token_str)
        if not db_token:
            return []
        return db.query(InteractionEvent).filter(InteractionEvent.token_id == db_token.id).all()
        
    @staticmethod
    def get_all_events(db: Session, org_id: uuid.UUID) -> list[InteractionEvent]:
        # returns all events for an organization
        return db.query(InteractionEvent).join(InteractionToken).filter(InteractionToken.org_id == org_id).all()
