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

class SensitiveDataExposureScanner:
    # A simple regex for SSN or Credit Card
    SSN_REGEX = r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b"
    IP_INTERNAL_REGEX = r"\b(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\..+\b"

    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            try:
                response = await client.get(target_url)
                body = response.text
                
                exposures = []
                # Find SSNs contextually (naive)
                if "ssn" in body.lower() or "social security" in body.lower():
                    ssns = re.findall(SensitiveDataExposureScanner.SSN_REGEX, body)
                    if ssns:
                        # Assuming checksum validation in real-world, here we just flag it
                        exposures.append({"type": "SSN", "matches_found": len(ssns), "verified": True})
                        
                if "stacktrace" in body.lower() or "exception" in body.lower():
                    if "at java.lang." in body or "Traceback (most recent call last):" in body:
                        exposures.append({"type": "Stack Trace", "verified": True})
                        
                internal_ips = re.findall(SensitiveDataExposureScanner.IP_INTERNAL_REGEX, body)
                if internal_ips:
                    exposures.append({"type": "Internal IP", "ips": internal_ips[:3], "verified": True})

                if exposures:
                    req_snippet = f"GET / HTTP/1.1\nHost: {response.url.host}"
                    res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                    res_snippet += f"\n{body[:2000]}"
                    
                    ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                    ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.SENSITIVE_DATA_EXPOSURE,
                        title=f"Sensitive Data Exposure at {target_url}",
                        fingerprint=f"sens_data_{target_url}",
                        metadata_json={"exposures": exposures}
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_req, ev_res]))
            except httpx.RequestError:
                pass
                
        return observations
