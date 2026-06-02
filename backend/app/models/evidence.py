import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class EvidenceType(str, enum.Enum):
    REQUEST = "request"
    RESPONSE = "response"
    SCREENSHOT = "screenshot"
    HTML_SNAPSHOT = "html_snapshot"
    DNS_RECORD = "dns_record"
    RAW_ARTIFACT = "raw_artifact"
    NETWORK_LOG = "network_log"
    TOOL_OUTPUT = "tool_output"
    OOB_CALLBACK = "oob_callback"

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    evidence_type = Column(Enum(EvidenceType, name="evidencetype", create_type=False), nullable=False, index=True)
    content_hash = Column(String(255), nullable=False, index=True)
    storage_path = Column(String(1024), nullable=True)
    snippet = Column(Text, nullable=True)
    validation_status = Column(String(50), nullable=True) # valid, invalid
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('org_id', 'content_hash', name='uq_evidence_org_hash'),
    )
