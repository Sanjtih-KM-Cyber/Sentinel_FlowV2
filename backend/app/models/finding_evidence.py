import uuid
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class FindingEvidence(Base):
    __tablename__ = "finding_evidence"

    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('finding_id', 'evidence_id', name='uq_finding_evidence'),
    )
