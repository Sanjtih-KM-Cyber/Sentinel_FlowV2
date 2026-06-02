import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.nmap_integration import NmapIntegration
from urllib.parse import urlparse

class PortDiscoveryScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        parsed = urlparse(target_url)
        target_host = parsed.hostname or target_url
        
        result = await NmapIntegration.run_scan(target_host)
        
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
            observation_type=ObservationType.OPEN_PORT,
            title=f"Port Discovery for {target_host}",
            fingerprint=f"open_ports_{target_host}",
            metadata_json={"open_ports": result.get("open_ports", [])}
        )
        obs = ObservationService.create_or_get_observation(db, obs_in, user)
        observations.append((obs, [ev_out]))
        
        return observations
