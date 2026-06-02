import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.wappalyzer_integration import WappalyzerIntegration

class TechFingerprintScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await WappalyzerIntegration.run_scan(target_url)
        techs = result.get("technologies", [])
        
        if techs:
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )

            for t in techs:
                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.TECHNOLOGY_FINGERPRINT,
                    title=f"Technology Fingerprint: {t['name']} on {target_url}",
                    fingerprint=f"tech_{t['name']}_{target_url}",
                    metadata_json={
                        "name": t.get("name"),
                        "confidence": t.get("confidence"),
                        "categories": t.get("categories"),
                        "version": t.get("version")
                    }
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_out]))
                
        return observations
