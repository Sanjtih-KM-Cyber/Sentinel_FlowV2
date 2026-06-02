import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.trufflehog_integration import TruffleHogIntegration

class HardcodedSecretScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, extract_dir: str, target_url: str, user: User) -> list:
        observations = []
        
        result = await TruffleHogIntegration.run_scan(extract_dir)
        secrets = result.get("secrets", [])
        
        if secrets:
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )
            
            for s in secrets:
                # Mask secret fully
                masked_val = "*" * 10
                if "Redacted" in s:
                    masked_val = s["Redacted"]

                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.HARDCODED_SECRET,
                    title=f"Hardcoded {s.get('DetectorName')} Secret",
                    fingerprint=f"secret_{s.get('DetectorName')}_{target_url}_{hash(s.get('File'))}",
                    metadata_json={
                        "secret_type": s.get("DetectorName"),
                        "file_path": s.get("File", ""),
                        "line_number": s.get("Line", 0),
                        "masked_secret": masked_val
                    }
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_out]))
                
        return observations
