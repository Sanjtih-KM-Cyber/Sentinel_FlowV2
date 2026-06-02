import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class AssetType(str, enum.Enum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    URL = "url"

class AssetStatus(str, enum.Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"
    ARCHIVED = "archived"

class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint('org_id', 'name', name='uq_asset_org_name'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    asset_type = Column(Enum(AssetType, name="assettype", create_type=False), nullable=False)
    status = Column(Enum(AssetStatus, name="assetstatus", create_type=False), default=AssetStatus.PENDING_VERIFICATION, nullable=False)
    
    is_archived = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", backref="assets")
    verifications = relationship("AssetVerification", back_populates="asset", cascade="all, delete-orphan")
