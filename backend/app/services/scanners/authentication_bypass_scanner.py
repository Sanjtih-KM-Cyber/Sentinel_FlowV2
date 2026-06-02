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
from app.services.mapping_services import AuthorizationContextService, DiscoveredEndpoint

class AuthenticationBypassScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        # 1. Discover protected resources via workflow or context
        protected_eps = db.query(DiscoveredEndpoint).filter_by(org_id=org_id, project_id=project_id).all()
        
        # Create contexts
        ctx_anon = AuthorizationContextService.get_context(db, org_id, project_id, "Anonymous")
        ctx_admin = AuthorizationContextService.get_context(db, org_id, project_id, "Admin")
        
        if not ctx_anon or not ctx_admin:
            return []
            
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for ep in protected_eps:
                try:
                    # Test Anonymous Access
                    res_anon = await client.request(ep.method, ep.url, headers=ctx_anon.headers)
                    # Baseline admin access
                    res_admin = await client.request(ep.method, ep.url, headers=ctx_admin.headers)
                    
                    # If anonymous gets same status and similar content length as admin
                    # or accessing protected features successfully
                    bypassed = res_anon.status_code == 200 and len(res_anon.text) > 0 and (abs(len(res_anon.text) - len(res_admin.text)) < 50 or "dashboard" in res_anon.text.lower())
                    
                    if bypassed:
                        req_snippet = f"{ep.method} {ep.url}\n"
                        res_snippet = f"HTTP/1.1 {res_anon.status_code} {res_anon.reason_phrase}\n{res_anon.text[:200]}"
                        
                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            observation_type=ObservationType.AUTHENTICATION_BYPASS,
                            title=f"Authentication Bypass at {ep.url}",
                            fingerprint=f"auth_bypass_{ep.url}",
                            metadata_json={
                                "endpoint": ep.url,
                                "bypassed": True,
                                "missing_auth_header": True
                            }
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res]))
                        
                except httpx.RequestError:
                    pass
                    
        return observations
