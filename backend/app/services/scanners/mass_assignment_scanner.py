import httpx
import uuid
import json
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.mapping_services import ParameterDiscoveryService, StateTrackingService, DiscoveredEndpoint

class MassAssignmentScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        from app.models.application_mapping import DiscoveredEndpoint, DiscoveredParameter
        
        ctx_user = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        if not ctx_user:
            return []
            
        # Find endpoints with parameters
        endpoints = db.query(DiscoveredEndpoint).filter_by(org_id=org_id, project_id=project_id).filter(
             DiscoveredEndpoint.method.in_(["POST", "PUT", "PATCH"])
        ).all()
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    # 1. State before
                    state_before = await StateTrackingService.capture_state(client, endpoint.url)
                    
                    hidden_params = [p for p in endpoint.parameters if p.is_hidden or p.name in ["is_admin", "role", "permissions"]]
                    if not hidden_params:
                         continue
                         
                    for param in hidden_params:
                        # 2. Mutation
                        payload = {**state_before, param.name: True}
                        
                        headers = ctx_user.headers or {}
                        cookies = ctx_user.cookies or {}
                        if "Content-Type" not in headers:
                             headers["Content-Type"] = "application/json"
                             
                        res_mutation = await client.request(endpoint.method, endpoint.url, json=payload, headers=headers, cookies=cookies)
                        
                        # 3. State after
                        state_after = await StateTrackingService.capture_state(client, endpoint.url)
                        
                        diff = StateTrackingService.generate_diff(state_before, state_after)
                        
                        # Check if the hidden param was actually added/changed in the persisted state
                        state_mutated = param.name in diff["added"] or param.name in diff["changed"]
                        
                        if res_mutation.status_code == 200 and state_mutated:
                            req_snippet = f"{endpoint.method} {endpoint.url}\n{json.dumps(payload)}"
                            res_snippet = f"HTTP/1.1 {res_mutation.status_code} {res_mutation.reason_phrase}\n{res_mutation.text[:200]}"
                            state_snippet = f"Diff: {json.dumps(diff)}"
                            
                            ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                            ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                            ev_state = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, state_snippet)

                            obs_in = ObservationCreate(
                                org_id=org_id,
                                project_id=project_id,
                                observation_type=ObservationType.MASS_ASSIGNMENT,
                                title=f"Mass Assignment via {param.name} at {endpoint.url}",
                                fingerprint=f"mass_assign_{endpoint.url}_{param.name}",
                                metadata_json={
                                    "endpoint": endpoint.url,
                                    "parameter": param.name,
                                    "state_mutated": True
                                }
                            )
                            obs = ObservationService.create_or_get_observation(db, obs_in, user)
                            observations.append((obs, [ev_req, ev_res, ev_state]))
                            break
                            
                except (httpx.RequestError, ValueError, Exception):
                    pass
                    
        return observations
