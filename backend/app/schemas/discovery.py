"""
Schemas for Discovery
"""
import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.discovery_job import DiscoveryStatus
from app.models.discovered_asset import AssetSource
from app.models.dns_record import DnsRecordType

# --- Technology Fingerprint ---

class TechnologyFingerprintBase(BaseModel):
    name: str
    category: Optional[str] = None
    version: Optional[str] = None

class TechnologyFingerprintCreate(TechnologyFingerprintBase):
    http_probe_id: uuid.UUID

class TechnologyFingerprint(TechnologyFingerprintBase):
    id: uuid.UUID
    http_probe_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- HTTP Probe ---

class HttpProbeBase(BaseModel):
    url: str
    status_code: Optional[int] = None
    title: Optional[str] = None
    content_length: Optional[int] = None
    server_header: Optional[str] = None

class HttpProbeCreate(HttpProbeBase):
    discovered_asset_id: uuid.UUID

class HttpProbe(HttpProbeBase):
    id: uuid.UUID
    discovered_asset_id: uuid.UUID
    created_at: datetime
    fingerprints: List[TechnologyFingerprint] = []
    model_config = ConfigDict(from_attributes=True)

# --- DNS Record ---

class DnsRecordBase(BaseModel):
    record_type: DnsRecordType
    value: str

class DnsRecordCreate(DnsRecordBase):
    discovered_asset_id: uuid.UUID

class DnsRecord(DnsRecordBase):
    id: uuid.UUID
    discovered_asset_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Discovered Asset ---

class DiscoveredAssetBase(BaseModel):
    name: str
    source: AssetSource

class DiscoveredAssetCreate(DiscoveredAssetBase):
    org_id: uuid.UUID
    discovery_job_id: uuid.UUID
    parent_asset_id: uuid.UUID

class DiscoveredAsset(DiscoveredAssetBase):
    id: uuid.UUID
    org_id: uuid.UUID
    discovery_job_id: uuid.UUID
    parent_asset_id: uuid.UUID
    created_at: datetime
    
    dns_records: List[DnsRecord] = []
    http_probes: List[HttpProbe] = []
    model_config = ConfigDict(from_attributes=True)

# --- Discovery Job ---

class DiscoveryJobBase(BaseModel):
    pass

class DiscoveryJobCreate(DiscoveryJobBase):
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID

class DiscoveryJobUpdate(BaseModel):
    status: Optional[DiscoveryStatus] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class DiscoveryJob(DiscoveryJobBase):
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID
    status: DiscoveryStatus
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
