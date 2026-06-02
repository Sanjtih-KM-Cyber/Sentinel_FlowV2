import httpx
import uuid
import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService

class HostHeaderScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        malicious_host = "evil.example.com"
        
        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            try:
                headers = {
                    "Host": malicious_host,
                    "X-Forwarded-Host": malicious_host
                }
                # e.g., reset link poisoning
                response = await client.get(target_url, headers=headers)
                
                req_snippet = f"GET / HTTP/1.1\nHost: {malicious_host}\nX-Forwarded-Host: {malicious_host}"
                res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                
                reflection_found = False
                for k, v in response.headers.items():
                    res_snippet += f"{k}: {v}\n"
                    if malicious_host in v:
                        reflection_found = True
                        
                body = response.text[:2000]
                res_snippet += f"\n{body}"
                
                # Check for absolute URLs or links poisoned
                if malicious_host in body:
                    # simplistic check for impactful reflection
                    if 'href="' in body or 'src="' in body or 'window.location' in body or 'Location:' in res_snippet:
                        reflection_found = True
                
                if reflection_found:
                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.HOST_HEADER_INJECTION,
                        title=f"Host Header Injection at {target_url}",
                        fingerprint=f"host_header_{target_url}",
                        metadata_json={
                            "injected_host": malicious_host,
                            "reflection_verified": True
                        }
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res]))
            except httpx.RequestError:
                pass
                
        return observations
