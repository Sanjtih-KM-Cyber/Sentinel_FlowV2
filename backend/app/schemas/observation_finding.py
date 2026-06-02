import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.models.verification_run import VerificationStatus
from app.models.finding import FindingStatus, Severity
from app.models.confidence_score import ConfidenceLevel

# --- Observation ---
class ObservationBase(BaseModel):
    observation_type: ObservationType
    title: str
    description: Optional[str] = None
    fingerprint: str
    metadata_json: Optional[Dict[str, Any]] = None

class ObservationCreate(ObservationBase):
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID

class Observation(ObservationBase):
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Evidence ---
class EvidenceBase(BaseModel):
    evidence_type: EvidenceType
    storage_path: Optional[str] = None
    snippet: Optional[str] = None

class EvidenceCreate(EvidenceBase):
    org_id: uuid.UUID
    content_hash: str

class Evidence(EvidenceBase):
    id: uuid.UUID
    org_id: uuid.UUID
    content_hash: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- VerificationRun ---
class VerificationRunBase(BaseModel):
    rule_id: str
    status: VerificationStatus
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class VerificationRunCreate(VerificationRunBase):
    org_id: uuid.UUID
    observation_id: uuid.UUID

class VerificationRun(VerificationRunBase):
    id: uuid.UUID
    org_id: uuid.UUID
    observation_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- ConfidenceScore ---
class ConfidenceScoreBase(BaseModel):
    level: ConfidenceLevel
    score_numerical: float
    reasoning: Optional[str] = None

class ConfidenceScoreCreate(ConfidenceScoreBase):
    org_id: uuid.UUID
    finding_id: uuid.UUID

class ConfidenceScore(ConfidenceScoreBase):
    id: uuid.UUID
    org_id: uuid.UUID
    finding_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Finding ---
class FindingBase(BaseModel):
    title: str
    description: Optional[str] = None
    remediation: Optional[str] = None
    status: FindingStatus
    severity: Severity
    metadata_json: Optional[Dict[str, Any]] = None

class FindingCreate(FindingBase):
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID
    observation_id: uuid.UUID

class FindingUpdate(BaseModel):
    status: Optional[FindingStatus] = None
    severity: Optional[Severity] = None

class Finding(FindingBase):
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: uuid.UUID
    observation_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    confidence_scores: List[ConfidenceScore] = []
    model_config = ConfigDict(from_attributes=True)
