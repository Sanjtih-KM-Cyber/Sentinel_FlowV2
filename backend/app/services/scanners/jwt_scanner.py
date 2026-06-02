import httpx
import base64
import json
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.models.user import User
import uuid

class JWTScanner:
    @staticmethod
    def extract_jwt_algo(token: str) -> str:
        try:
            parts = token.split('.')
            if len(parts) == 3:
                header_padded = parts[0] + '=' * (-len(parts[0]) % 4)
                header_json = base64.b64decode(header_padded).decode('utf-8')
                header = json.loads(header_json)
                return header.get('alg', '')
        except Exception:
            pass
        return ''

    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, base_url: str, user: User) -> list:
        observations = []
        from app.models.application_mapping import DiscoveredEndpoint
        from app.services.mapping_services import AuthorizationContextService
        
        ctx_user = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        if not ctx_user or not ctx_user.headers or "Authorization" not in ctx_user.headers:
            return []
            
        auth_header = ctx_user.headers["Authorization"]
        if not auth_header.startswith("Bearer "):
            return []
            
        token = auth_header.replace("Bearer ", "")
        
        eps = db.query(DiscoveredEndpoint).filter_by(org_id=org_id, project_id=project_id, is_api=True).all()
        if not eps:
             return []

        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            for ep in eps:
                try:
                    # Test 'none' algorithm
                    parts = token.split('.')
                    if len(parts) == 3:
                        header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip('=')
                        payload = parts[1] # Keep the original payload (maybe modify "sub" to admin later)
                        none_token = f"{header}.{payload}."
                        
                        headers = {"Authorization": f"Bearer {none_token}"}
                        response = await client.request(ep.method, ep.url, headers=headers)
                        
                        # If a protected API endpoint accepts the 'none' token, it's vulnerable
                        if response.status_code in [200, 201] and len(response.text) > 0 and "error" not in response.text.lower():
                            algo = "none"
                            req_snippet = f"{ep.method} {ep.url} HTTP/1.1\nHost: {response.url.host}\nAuthorization: Bearer {none_token}"
                            res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n{response.text[:200]}"
                            
                            ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                            ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
            
                            obs_in = ObservationCreate(
                                org_id=org_id,
                                project_id=project_id,
                                asset_id=asset_id,
                                observation_type=ObservationType.JWT_ISSUE,
                                title=f"JWT None Algorithm Accepted at {ep.url}",
                                fingerprint=f"jwt_none_{ep.url}",
                                metadata_json={"algorithm": algo}
                            )
                            obs = ObservationService.create_or_get_observation(db, obs_in, user)
                            observations.append((obs, [ev_req, ev_res]))
                            break

                except httpx.RequestError:
                    pass
        return observations
