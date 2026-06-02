import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class AssetSource(str, enum.Enum):
    CRT_SH = "crt_sh"
    HACKERTARGET = "hackertarget"
    MANUAL = "manual"
    PASSIVE_DNS = "passive_dns"

class DiscoveredAsset(Base):
    __tablename__ = "discovered_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    discovery_job_id = Column(UUID(as_uuid=True), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    source = Column(Enum(AssetSource, name="assetsource", create_type=False), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('parent_asset_id', 'name', name='uq_discovered_asset_parent_name'),
    )

    discovery_job = relationship("DiscoveryJob", back_populates="discovered_assets")
    dns_records = relationship("DnsRecord", back_populates="discovered_asset", cascade="all, delete-orphan")
    http_probes = relationship("HttpProbe", back_populates="discovered_asset", cascade="all, delete-orphan")
