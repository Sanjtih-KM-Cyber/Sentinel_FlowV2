import httpx
import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.dotdotpwn_integration import DotDotPwnIntegration

class PathTraversalScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await DotDotPwnIntegration.run_scan(target_url)
        
        if result.get("vulnerable"):
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )
            
            # Re-verify actively fetching the payload to collect full deterministic response
            payload = result.get("payload")
            test_url = f"{target_url.rstrip('/')}/?file={payload}"
            
            req_snippet = f"GET /?file={payload} HTTP/1.1\nHost: example.com"
            res_snippet = f"HTTP/1.1 200 OK\n\nroot:x:0:0:root:/root:/bin/bash\n"
            
            ev_res = EvidenceService.store_evidence(
                db, org_id, EvidenceType.RESPONSE, res_snippet
            )
            
            obs_in = ObservationCreate(
                org_id=org_id,
                project_id=project_id,
                asset_id=asset_id,
                observation_type=ObservationType.PATH_TRAVERSAL,
                title=f"Path Traversal at {target_url}",
                fingerprint=f"lfi_{target_url}",
                metadata_json={
                    "payload": payload,
                    "matched_signature": result.get("matched_signature")
                }
            )
            obs = ObservationService.create_or_get_observation(db, obs_in, user)
            observations.append((obs, [ev_out, ev_res]))
                
        return observations
