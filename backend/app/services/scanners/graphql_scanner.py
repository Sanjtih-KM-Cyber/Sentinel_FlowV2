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
from app.services.mapping_services import JavaScriptAnalysisService, ParameterDiscoveryService

class GraphQLSecurityScanner:
    @staticmethod
    async def scan(target_url: str, db: Session, org_id: uuid.UUID, project_id: uuid.UUID, user: User) -> List[Tuple]:
        observations = []
        
        from app.models.application_mapping import DiscoveredEndpoint
        
        gql_endpoints = db.query(DiscoveredEndpoint).filter_by(org_id=org_id, project_id=project_id).filter(
            DiscoveredEndpoint.url.ilike("%graphql%")
        ).all()
        
        if not gql_endpoints:
            return []

        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for ep in gql_endpoints:
                # 2. Introspection
                introspection_query = {
                    "query": "\n    query IntrospectionQuery {\n      __schema {\n        queryType { name }\n        mutationType { name }\n      }\n    }\n  "
                }

                try:
                    res_intro = await client.post(ep.url, json=introspection_query, follow_redirects=False)
                    if res_intro.status_code == 200 and "__schema" in res_intro.text:
                        
                        ParameterDiscoveryService.discover_parameters(
                            db, ep.id, url=ep.url, method="POST", body=json.dumps(introspection_query),
                            headers={"Content-Type": "application/json"}
                        )
                        
                        req_snippet = f"POST {ep.url}\n{json.dumps(introspection_query)}"
                        res_snippet = f"HTTP/1.1 {res_intro.status_code} {res_intro.reason_phrase}\n{res_intro.text[:500]}"
                        
                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            observation_type=ObservationType.GRAPHQL_SECURITY,
                            title=f"GraphQL Introspection Enabled at {ep.url}",
                            fingerprint=f"graphql_intro_{ep.url}",
                            metadata_json={
                                "issue_type": "introspection",
                                "is_vulnerable": False
                            }
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res]))
                except httpx.RequestError:
                    pass

                # 3. Query Complexity testing
                complexity_query = {
                    "query": "query { user { posts { author { posts { author { id } } } } } }"
                }
                try:
                    res_comp = await client.post(ep.url, json=complexity_query, follow_redirects=False)
                    if res_comp.status_code == 200 and "errors" not in res_comp.json():
                        req_snippet = f"POST {ep.url}\n{json.dumps(complexity_query)}"
                        res_snippet = f"HTTP/1.1 {res_comp.status_code} {res_comp.reason_phrase}\n{res_comp.text[:500]}"
                        
                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            observation_type=ObservationType.GRAPHQL_SECURITY,
                            title=f"GraphQL Lack of Query Complexity Limits at {ep.url}",
                            fingerprint=f"graphql_complexity_{ep.url}",
                            metadata_json={
                                "issue_type": "complexity",
                                "is_vulnerable": True
                            }
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res]))

                except httpx.RequestError:
                    pass
                    
        return observations
