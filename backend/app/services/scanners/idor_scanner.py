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
from app.services.mapping_services import ObjectDiscoveryService, AuthorizationContextService, DiscoveredEndpoint

class IDORScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        # 1. Context mapping
        context_a = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        context_b = AuthorizationContextService.get_context(db, org_id, project_id, "UserB")

        if not context_a or not context_b:
            return []
        
        objects_a = db.query(ObjectDiscoveryService).filter_by(owner_context="UserA").all() if False else [] # Actually DiscoveredObject
        from app.models.application_mapping import DiscoveredObject
        
        objects_a = db.query(DiscoveredObject).filter_by(org_id=org_id, project_id=project_id, owner_context="UserA").all()
        
        if not objects_a:
            return []
            
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for target_obj in objects_a:
                if not target_obj.source_endpoint_id:
                     continue
                ep = db.query(DiscoveredEndpoint).get(target_obj.source_endpoint_id)
                if not ep:
                     continue
                     
                obj_url = f"{ep.url}/{target_obj.identifier}"
                try:
                    # 3. Cross-User Access Validation
                    res_b = await client.request(ep.method, obj_url, headers=context_b.headers)
                
                if res_b.status_code == 200 and len(res_b.text) > 0 and "error" not in res_b.text.lower():
                    # Cross-user access worked!
                    req_snippet = f"GET {obj_url}\nAuthorization: {context_b.headers.get('Authorization')}"
                    res_snippet = f"HTTP/1.1 {res_b.status_code} {res_b.reason_phrase}\n{res_b.text[:200]}"
                    
                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        observation_type=ObservationType.IDOR,
                        title=f"Insecure Direct Object Reference at {obj_url}",
                        fingerprint=f"idor_{obj_url}",
                        metadata_json={
                            "endpoint": obj_url,
                            "object_id": target_obj.identifier,
                            "cross_user_access": True,
                            "owner": "UserA",
                            "accessor": "UserB"
                        }
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res]))
                    
            except httpx.RequestError:
                pass
                    
        return observations
