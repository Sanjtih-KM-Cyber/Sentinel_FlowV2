import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DnsRecordType(str, enum.Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"

class DnsRecord(Base):
    __tablename__ = "dns_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    discovered_asset_id = Column(UUID(as_uuid=True), ForeignKey("discovered_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    record_type = Column(Enum(DnsRecordType, name="dnsrecordtype", create_type=False), nullable=False)
    value = Column(String(1024), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    discovered_asset = relationship("DiscoveredAsset", back_populates="dns_records")
