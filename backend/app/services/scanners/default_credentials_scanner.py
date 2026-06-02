import httpx
import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService

class DefaultCredentialsScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        credentials = [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "root")
        ]
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for username, password in credentials:
                try:
                    payload = {"username": username, "password": password}
                    response = await client.post(f"{target_url}/login", json=payload, follow_redirects=False)
                    
                    # 200 is not enough, must check for session token or auth indicator
                    cookies = response.cookies
                    has_session = "session" in cookies or "token" in response.text
                    
                    if response.status_code == 200 and has_session:
                        
                        req_snippet = f"POST {target_url}/login\n{payload}"
                        res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\nSet-Cookie: {response.headers.get('set-cookie')}\n{response.text[:200]}"
                        
                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                        
                        # Store session validation evidence
                        validation_snippet = "Session validation confirmed via received session cookie/token."
                        ev_val = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, validation_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            observation_type=ObservationType.DEFAULT_CREDENTIALS,
                            title=f"Default Credentials found at {target_url}",
                            fingerprint=f"default_creds_{target_url}_{username}",
                            metadata_json={
                                "username": username,
                                "password": password,
                                "endpoint": f"{target_url}/login",
                                "authenticated": True
                            }
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res, ev_val]))
                        break # Found valid creds
                        
                except httpx.RequestError:
                    pass
                    
        return observations
