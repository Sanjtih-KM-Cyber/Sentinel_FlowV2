import httpx
import uuid
import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService

class ClickjackingScanner:
    STATE_CHANGING_KEYWORDS = ["submit", "save", "update", "delete", "post", "password", "login"]
    
    @staticmethod
    def _is_state_changing(html_content: str) -> bool:
        # Simple heuristic to find forms or sensitive keywords
        content_lower = html_content.lower()
        if "<form" in content_lower:
            for kw in ClickjackingScanner.STATE_CHANGING_KEYWORDS:
                if kw in content_lower:
                    return True
        return False

    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=5.0) as client:
            try:
                response = await client.get(target_url)
                
                headers = response.headers
                xfo = headers.get("x-frame-options", "").lower()
                csp = headers.get("content-security-policy", "").lower()
                
                missing_protection = True
                if xfo in ["deny", "sameorigin"]:
                    missing_protection = False
                if "frame-ancestors" in csp:
                    # Very simple check, doesn't parse complex CSPs
                    missing_protection = False
                    
                is_state_changing = ClickjackingScanner._is_state_changing(response.text)
                
                req_snippet = f"GET / HTTP/1.1\nHost: {response.url.host}"
                res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                for k, v in headers.items():
                    res_snippet += f"{k}: {v}\n"
                res_snippet += f"\n{response.text[:1000]}"

                ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.CLICKJACKING,
                    title=f"Clickjacking Analysis for {target_url}",
                    fingerprint=f"clickjacking_{target_url}",
                    metadata_json={
                        "missing_protection": missing_protection,
                        "xfo_header": xfo,
                        "csp_header": csp,
                        "is_state_changing": is_state_changing
                    }
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_req, ev_res]))
            except httpx.RequestError:
                pass
                
        return observations
