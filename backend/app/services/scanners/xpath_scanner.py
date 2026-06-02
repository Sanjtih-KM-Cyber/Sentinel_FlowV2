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

class XPathInjectionScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        from app.models.application_mapping import DiscoveredEndpoint, DiscoveredParameter
        
        endpoints = db.query(DiscoveredEndpoint).filter_by(org_id=org_id, project_id=project_id).filter(
            DiscoveredEndpoint.method.in_(["GET", "POST", "PUT"])
        ).all()
        
        payloads = [
            ({"val": "'] or '1'='1"}, "boolean"),
            ({"val": "' or 1=1 or ''='"}, "boolean"),
            ({"val": "']][["}, "error")
        ]
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for ep in endpoints:
                if not ep.parameters:
                    continue
                for p in ep.parameters:
                    for payload_data, vuln_type in payloads:
                        try:
                            # 1. Baseline Request
                            req_data = {param.name: param.default_value or "test" for param in ep.parameters}
                            
                            # 2. Injected Request
                            inj_data = req_data.copy()
                            inj_data[p.name] = payload_data["val"]
                            
                            response = None
                            if ep.method == "GET":
                                 baseline_res = await client.request(ep.method, ep.url, params=req_data)
                                 response = await client.request(ep.method, ep.url, params=inj_data)
                            else:
                                 if ep.is_api:
                                     baseline_res = await client.request(ep.method, ep.url, json=req_data)
                                     response = await client.request(ep.method, ep.url, json=inj_data)
                                 else:
                                     baseline_res = await client.request(ep.method, ep.url, data=inj_data)
                                     response = await client.request(ep.method, ep.url, data=inj_data)
                            
                            is_vulnerable = False
                            
                            if vuln_type == "error" and response.status_code == 500:
                                 if "XPathException" in response.text or "Invalid expression" in response.text:
                                     is_vulnerable = True
                            elif vuln_type == "boolean":
                                 if response.status_code == 200 and baseline_res.status_code == 200:
                                      if len(response.text) != len(baseline_res.text) and abs(len(response.text) - len(baseline_res.text)) > 100:
                                          is_vulnerable = True

                            if is_vulnerable:
                                req_snippet = f"{ep.method} {ep.url}\nPayload: {payload_data['val']}"
                                res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n{response.text[:500]}"
                                
                                ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                                ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                                obs_in = ObservationCreate(
                                    org_id=org_id,
                                    project_id=project_id,
                                    observation_type=ObservationType.XPATH_INJECTION,
                                    title=f"XPath Injection at {ep.url} via {p.name}",
                                    fingerprint=f"xpath_{ep.url}_{p.name}_{vuln_type}",
                                    metadata_json={
                                        "payload": payload_data["val"],
                                        "vuln_type": vuln_type,
                                        "parameter": p.name
                                    }
                                )
                                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                                observations.append((obs, [ev_req, ev_res]))
                                
                        except httpx.RequestError:
                            pass
                    
        return observations
