import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TechnologyFingerprint(Base):
    __tablename__ = "technology_fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    http_probe_id = Column(UUID(as_uuid=True), ForeignKey("http_probes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False) # e.g., "Nginx", "WordPress", "React"
    category = Column(String(255), nullable=True) # e.g., "Web Server", "CMS", "Frontend Framework"
    version = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    http_probe = relationship("HttpProbe", back_populates="fingerprints")
