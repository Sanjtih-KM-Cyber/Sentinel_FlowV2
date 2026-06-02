import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class HttpProbe(Base):
    __tablename__ = "http_probes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    discovered_asset_id = Column(UUID(as_uuid=True), ForeignKey("discovered_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    url = Column(String(2048), nullable=False)
    status_code = Column(Integer, nullable=True)
    title = Column(String(512), nullable=True)
    content_length = Column(Integer, nullable=True)
    server_header = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    discovered_asset = relationship("DiscoveredAsset", back_populates="http_probes")
    fingerprints = relationship("TechnologyFingerprint", back_populates="http_probe", cascade="all, delete-orphan")
