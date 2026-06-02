import httpx
import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService

class HttpMethodScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for method in ["TRACE", "TRACK"]:
                try:
                    response = await client.request(method, target_url)
                    
                    req_snippet = f"{method} / HTTP/1.1\nHost: {response.url.host}"
                    res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                    for k, v in response.headers.items():
                        res_snippet += f"{k}: {v}\n"
                    res_snippet += f"\n{response.text[:1000]}"

                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.HTTP_TRACE_ENABLED,
                        title=f"HTTP Method {method} allowed at {target_url}",
                        fingerprint=f"http_method_{method}_{target_url}"
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res]))
                except httpx.RequestError:
                    pass
                    
        return observations
