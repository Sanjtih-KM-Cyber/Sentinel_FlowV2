import httpx
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.models.user import User
import uuid

class SensitiveFileScanner:
    TARGET_PATHS = [
        "/.env", "/.env.local", "/.env.production",
        "/.git/config", "/.git/HEAD",
        "/backup.zip", "/backup.tar.gz",
        "/config.php.bak", "/config.bak",
        "/database.sql", "/dump.sql"
    ]

    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, base_url: str, user: User) -> list:
        observations = []
        async with httpx.AsyncClient(verify=False, follow_redirects=False, timeout=5.0) as client:
            for path in SensitiveFileScanner.TARGET_PATHS:
                target_url = f"{base_url.rstrip('/')}{path}"
                try:
                    response = await client.get(target_url)
                    if response.status_code == 200 and response.text:
                        req_snippet = f"GET {path} HTTP/1.1\nHost: {response.url.host}"
                        res_snippet = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\n"
                        for k, v in response.headers.items():
                            res_snippet += f"{k}: {v}\n"
                        res_snippet += f"\n{response.text[:2000]}"

                        ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                        ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)

                        obs_in = ObservationCreate(
                            org_id=org_id,
                            project_id=project_id,
                            asset_id=asset_id,
                            observation_type=ObservationType.EXPOSED_FILE,
                            title=f"Potential Sensitive File Exposed: {path}",
                            fingerprint=f"exposed_file_{path}"
                        )
                        obs = ObservationService.create_or_get_observation(db, obs_in, user)
                        observations.append((obs, [ev_req, ev_res]))
                except httpx.RequestError:
                    pass
        return observations
