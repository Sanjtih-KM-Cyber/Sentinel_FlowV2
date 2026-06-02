import httpx
import uuid
import urllib.parse
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService

class CRLFInjectionScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, base_url: str, user: User) -> list:
        observations = []
        
        payloads = [
            "%0d%0aSet-Cookie:crlf=injection"
        ]
        
        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            for p in payloads:
                target = f"{base_url.rstrip('/')}/?q={p}"
                try:
                    response = await client.get(target)
                    req_snippet = f"GET /?q={p} HTTP/1.1\nHost: {response.url.host}"
                    res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                    
                    injected_header_found = False
                    for k, v in response.headers.items():
                        res_snippet += f"{k}: {v}\n"
                        if k.lower() == "set-cookie" and "crlf=injection" in v:
                            injected_header_found = True
                            
                    res_snippet += f"\n{response.text[:200]}"
                    
                    if injected_header_found:
                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            asset_id=asset_id,
                            observation_type=ObservationType.CRLF_INJECTION,
                            title=f"CRLF Injection at {base_url}",
                            fingerprint=f"crlf_{base_url}",
                            metadata_json={
                                "payload": urllib.parse.unquote(p),
                                "injected_header": "Set-Cookie: crlf=injection"
                            }
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res]))
                except httpx.RequestError:
                    pass
                
        return observations
