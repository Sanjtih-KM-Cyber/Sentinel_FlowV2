import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class InteractionToken(Base):
    __tablename__ = "interaction_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    source_module = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    events = relationship("InteractionEvent", back_populates="token", cascade="all, delete-orphan")

class InteractionEvent(Base):
    __tablename__ = "interaction_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token_id = Column(UUID(as_uuid=True), ForeignKey("interaction_tokens.id"), nullable=False)
    protocol = Column(String, nullable=False)
    source_ip = Column(String, nullable=False)
    request_headers = Column(JSONB, nullable=True)
    request_body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    token = relationship("InteractionToken", back_populates="events")
