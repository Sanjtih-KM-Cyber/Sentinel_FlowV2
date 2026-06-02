import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ConfidenceLevel(str, enum.Enum):
    CERTAIN = "certain"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TENTATIVE = "tentative"

class ConfidenceScore(Base):
    __tablename__ = "confidence_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    level = Column(Enum(ConfidenceLevel, name="confidencelevel", create_type=False), nullable=False)
    score_numerical = Column(Float, nullable=False) # e.g., 0.0 to 1.0
    reasoning = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
