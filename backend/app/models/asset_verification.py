import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class VerificationMethod(str, enum.Enum):
    DNS_TXT = "dns_txt"
    HTML_FILE = "html_file"
    META_TAG = "meta_tag"

class AssetVerification(Base):
    __tablename__ = "asset_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    method = Column(Enum(VerificationMethod, name="verificationmethod", create_type=False), nullable=False)
    verification_token = Column(String(255), nullable=False, unique=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="verifications")
