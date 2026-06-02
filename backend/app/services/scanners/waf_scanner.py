import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.wafw00f_integration import Wafw00fIntegration

class WafScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await Wafw00fIntegration.run_scan(target_url)
        
        if result.get("detected"):
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
                observation_type=ObservationType.WAF_DETECTED,
                title=f"WAF Detected: {result.get('vendor')} for {target_url}",
                fingerprint=f"waf_{result.get('vendor')}_{target_url}",
                metadata_json={
                    "detected": result.get("detected"), 
                    "vendor": result.get("vendor"),
                    "confidence": result.get("confidence")
                }
            )
            obs = ObservationService.create_or_get_observation(db, obs_in, user)
            observations.append((obs, [ev_out]))
        
        return observations
