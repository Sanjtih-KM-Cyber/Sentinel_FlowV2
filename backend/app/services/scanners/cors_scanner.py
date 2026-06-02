import httpx
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.models.user import User
import uuid

class CORSScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, base_url: str, user: User) -> list:
        observations = []
        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            target_url = f"{base_url.rstrip('/')}/api/data"  # Example target
            try:
                headers = {"Origin": "http://evil.com"}
                response = await client.get(target_url, headers=headers)
                
                req_snippet = f"GET /api/data HTTP/1.1\nHost: {response.url.host}\nOrigin: http://evil.com"
                res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                for k, v in response.headers.items():
                    res_snippet += f"{k}: {v}\n"

                ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.CORS_MISCONFIG,
                    title=f"Potential CORS Misconfiguration at {base_url}",
                    fingerprint=f"cors_misconfig_{base_url}"
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_req, ev_res]))
            except httpx.RequestError:
                pass
        return observations
