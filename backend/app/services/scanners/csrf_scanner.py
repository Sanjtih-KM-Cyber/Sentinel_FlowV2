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
from app.services.mapping_services import FormDiscoveryService, StateTrackingService

class CSRFScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        from app.models.application_mapping import DiscoveredEndpoint
        
        ctx_user = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        if not ctx_user:
             return []
             
        form_endpoints = db.query(DiscoveredEndpoint).filter_by(
            org_id=org_id, project_id=project_id, is_form=True
        ).all()
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for endpoint in form_endpoints:
                try:
                    if endpoint.method.upper() in ["POST", "PUT", "DELETE"]:
                        # 2. Extract CSRF token parameter (or lack thereof)
                        params = endpoint.parameters
                        csrf_params = [p for p in params if "csrf" in p.name.lower() or "token" in p.name.lower()]
                        
                        # Prepare payload without CSRF token
                        payload = {}
                        for p in params:
                            if p not in csrf_params:
                                payload[p.name] = p.default_value or "test"
                                
                        # Capture state before using a GET on the form's URL as approximation
                        state_before = await StateTrackingService.capture_state(client, endpoint.url)
                        
                        # Replay without token
                        headers = ctx_user.headers or {}
                        cookies = ctx_user.cookies or {}
                        if "Content-Type" not in headers:
                             headers["Content-Type"] = "application/x-www-form-urlencoded"
                             
                        res_mut = await client.request(
                            endpoint.method, endpoint.url, data=payload, headers=headers, cookies=cookies
                        )
                        
                        # Capture state after
                        state_after = await StateTrackingService.capture_state(client, endpoint.url)
                        diff = StateTrackingService.generate_diff(state_before, state_after)
                        
                        action_succeeded = res_mut.status_code in [200, 302] and (diff["added"] or diff["changed"] or diff["removed"] or "updated" in res_mut.text.lower())
                        
                        if action_succeeded:
                            req_snippet = f"{endpoint.method} {endpoint.url}\nCookies: {cookies}\n{json.dumps(payload)}"
                            res_snippet = f"HTTP/1.1 {res_mut.status_code} {res_mut.reason_phrase}\n{res_mut.text[:200]}"
                            
                            ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                            ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                            obs_in = ObservationCreate(
                                org_id=org_id,
                                project_id=project_id,
                                observation_type=ObservationType.CSRF,
                                title=f"Cross-Site Request Forgery at {endpoint.url}",
                                fingerprint=f"csrf_{endpoint.url}",
                                metadata_json={
                                    "endpoint": endpoint.url,
                                    "action_succeeded": True,
                                    "missing_token": True,
                                    "diff": diff
                                }
                            )
                            obs = ObservationService.create_or_get_observation(db, obs_in, user)
                            observations.append((obs, [ev_req, ev_res]))
                        
                except httpx.RequestError:
                    pass
                    
        return observations
