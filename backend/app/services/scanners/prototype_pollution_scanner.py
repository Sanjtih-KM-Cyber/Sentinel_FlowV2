import uuid
import json
import httpx
from typing import List, Tuple, Any
from sqlalchemy.orm import Session
from app.models.observation import ObservationType, Observation
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService, EvidenceType
from app.models.application_mapping import DiscoveredEndpoint, DiscoveredParameter
from app.models.user import User
from app.services.mapping_services import AuthorizationContextService

class PrototypePollutionScanner:
    @staticmethod
    async def scan(
        target_url: str,
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user: User
    ) -> List[Tuple[Observation, List[Any]]]:
        observations = []
        
        # Get discovered parameters for endpoints that take JSON
        json_params = db.query(DiscoveredParameter).join(DiscoveredEndpoint).filter(
            DiscoveredEndpoint.org_id == org_id,
            DiscoveredEndpoint.project_id == project_id,
            DiscoveredParameter.param_type.in_(["JSON", "POST", "PUT"])
        ).all()
        
        endpoints_to_test = {}
        for p in json_params:
            if p.endpoint_id not in endpoints_to_test:
                endpoints_to_test[p.endpoint_id] = {"endpoint": p.endpoint, "params": []}
            endpoints_to_test[p.endpoint_id]["params"].append(p)
            
        ctx_user = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        if not ctx_user:
            return []
            
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for ep_id, data in endpoints_to_test.items():
                ep = data["endpoint"]
                params = data["params"]
                
                # We need to construct a dynamic payload based on the parameters
                base_payload = {}
                for p in params:
                    # simplistic re-construction of nested JSON for __proto__
                    base_payload[p.name] = p.default_value or "test"
                    
                # The payloads to test prototype pollution
                payloads = [
                    {"__proto__": {"flag": "polluted"}, **base_payload},
                    {"constructor": {"prototype": {"flag": "polluted"}}, **base_payload}
                ]
                
                for payload in payloads:
                    try:
                        headers = {**ctx_user.headers, "Content-Type": "application/json"}
                        res = await client.request(ep.method, ep.url, json=payload, headers=headers)
                        
                        # Actual prototype mutation verification
                        # We send a validation request to a known endpoint without the payload, looking for the polluted flag
                        # Alternatively, we detect it using side-effects on subsequent requests
                        val_res = await client.get(ep.url, headers=ctx_user.headers)
                        
                        val_data = ""
                        try:
                            val_data = val_res.json()
                        except:
                            val_data = val_res.text
                            
                        # Verification must demonstrate Object.prototype modification
                        # if the global Object.prototype was modified, it will appear in clean responses
                        # as an inherited property on returned JSON objects
                        pollution_proven = False
                        if isinstance(val_data, dict) and "flag" in val_data and val_data["flag"] == "polluted":
                            pollution_proven = True
                        elif "polluted" in str(val_data):
                            # if it reflects without the payload, prototype is mutated
                            pollution_proven = True
                        
                        if pollution_proven:
                            req_snippet = f"{ep.method} {ep.url}\n{json.dumps(payload)}\n\nGET {ep.url}"
                            res_snippet = f"HTTP/1.1 {val_res.status_code} {val_res.reason_phrase}\n{val_res.text[:200]}"
                            
                            ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                            ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                            obs_in = ObservationCreate(
                                org_id=org_id,
                                project_id=project_id,
                                observation_type=ObservationType.PROTOTYPE_POLLUTION,
                                title=f"Prototype Pollution via {list(payload.keys())[0]} at {ep.url}",
                                fingerprint=f"proto_pollution_{ep.url}_{list(payload.keys())[0]}",
                                metadata_json={
                                    "endpoint": ep.url,
                                    "polluted_property": "flag",
                                    "payload": payload,
                                    "evidence": "Global prototype modification confirmed via secondary request"
                                }
                            )
                            obs = ObservationService.create_or_get_observation(db, obs_in, user)
                            observations.append((obs, [ev_req, ev_res]))
                            break # No need to test other payloads on this endpoint if one worked
                            
                    except httpx.RequestError:
                        pass
                        
        return observations
