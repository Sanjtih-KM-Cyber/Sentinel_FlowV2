import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.ffuf_integration import FfufIntegration

class ApiEndpointScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await FfufIntegration.run_scan(target_url)
        endpoints = result.get("endpoints", [])
        
        if endpoints:
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                f"Discovered {len(endpoints)} endpoints via FFuf. Example: {endpoints[0]['url']}"
            )

            obs_in = ObservationCreate(
                org_id=org_id,
                project_id=project_id,
                asset_id=asset_id,
                observation_type=ObservationType.API_ENDPOINT,
                title=f"API Endpoint Enumeration for {target_url}",
                fingerprint=f"api_enum_{target_url}",
                metadata_json={"endpoints": endpoints}
            )
            obs = ObservationService.create_or_get_observation(db, obs_in, user)
            observations.append((obs, [ev_out]))
                
        return observations
