import httpx
import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.schemas.interaction import InteractionTokenCreate
from app.services.interaction_service import InteractionService
from app.core.config import settings

class XXEScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User, oob_domain: str = "oob.local") -> list:
        observations = []
        
        token_in = InteractionTokenCreate(org_id=org_id, project_id=project_id, source_module="XXE")
        db_token = InteractionService.generate_token(db, token_in)
        
        base_domain = settings.OOB_DOMAIN if hasattr(settings, "OOB_DOMAIN") else "localhost:3000/api/oob"
        interaction_url = f"http://{base_domain}/{db_token.token}"
        
        payload = f"""<?xml version="1.0" encoding="ISO-8859-1"?>\n<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "{interaction_url}"> ]>\n<foo>&xxe;</foo>"""

        headers = {"Content-Type": "application/xml"}
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            try:
                response = await client.post(target_url, content=payload, headers=headers)
                
                # Verification must rely on InteractionEvents
                events = InteractionService.get_events_for_token(db, db_token.token)
                
                if events:
                    req_snippet = f"POST / HTTP/1.1\nHost: {response.url.host}\nContent-Type: application/xml\n\n{payload}"
                    res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                    for k, v in response.headers.items():
                        res_snippet += f"{k}: {v}\n"
                        
                    oob_evidence = f"Interaction Service confirmed OOB callback for token {db_token.token} with {len(events)} events."
                    
                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                    ev_oob = EvidenceService.store_evidence(db, org_id, EvidenceType.TOOL_OUTPUT, oob_evidence)
    
                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.XXE,
                        title=f"XXE Vulnerability at {target_url}",
                        fingerprint=f"xxe_{target_url}",
                        metadata_json={
                            "payload": payload,
                            "oob_token": db_token.token,
                            "verified_by_oob": True
                        }
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res, ev_oob]))
            except httpx.RequestError:
                pass
                
        return observations
