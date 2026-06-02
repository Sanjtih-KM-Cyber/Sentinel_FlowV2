import httpx
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.models.user import User
import uuid

class OpenRedirectScanner:
    PAYLOADS = [
        "?redirect=http://evil.com", "?next=http://evil.com",
        "?url=http://evil.com", "?target=http://evil.com"
    ]

    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, base_url: str, user: User) -> list:
        observations = []
        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            for payload in OpenRedirectScanner.PAYLOADS:
                target_url = f"{base_url.rstrip('/')}/login{payload}"
                try:
                    response = await client.get(target_url)
                    
                    req_snippet = f"GET /login{payload} HTTP/1.1\nHost: {response.url.host}"
                    res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                    for k, v in response.headers.items():
                        res_snippet += f"{k}: {v}\n"

                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.OPEN_REDIRECT,
                        title=f"Potential Open Redirect at {payload}",
                        fingerprint=f"open_redirect_{payload}"
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res]))
                except httpx.RequestError:
                    pass
        return observations
