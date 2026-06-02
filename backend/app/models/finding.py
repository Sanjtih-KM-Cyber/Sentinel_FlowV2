import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class FindingStatus(str, enum.Enum):
    POTENTIAL = "potential"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    RETEST_PENDING = "retest_pending"
    CLOSED = "closed"
    SUPPRESSED = "suppressed"

class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(UUID(as_uuid=True), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    
    status = Column(Enum(FindingStatus, name="findingstatus", create_type=False), default=FindingStatus.POTENTIAL, nullable=False, index=True)
    severity = Column(Enum(Severity, name="severity", create_type=False), nullable=False, index=True)
    
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    confidence_scores = relationship("ConfidenceScore", backref="finding", cascade="all, delete-orphan")
