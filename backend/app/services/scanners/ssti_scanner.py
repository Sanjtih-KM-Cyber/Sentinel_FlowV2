import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.tplmap_integration import TplMapIntegration

class SSTIScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await TplMapIntegration.run_scan(target_url)
        
        if result.get("vulnerable"):
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )
            
            obs_in = ObservationCreate(
                org_id=org_id,
                project_id=project_id,
                asset_id=asset_id,
                observation_type=ObservationType.SSTI,
                title=f"SSTI ({result.get('engine')}) at {target_url}",
                fingerprint=f"ssti_{target_url}",
                metadata_json={
                    "vulnerable": True,
                    "engine": result.get("engine"),
                    "payload": result.get("payload"),
                    "execution_evidence": result.get("execution_evidence")
                }
            )
            obs = ObservationService.create_or_get_observation(db, obs_in, user)
            observations.append((obs, [ev_out]))
        
        return observations
