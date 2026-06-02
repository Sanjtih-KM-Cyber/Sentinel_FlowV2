import socket
import ssl
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.models.user import User
import uuid

class TLSScanner:
    @staticmethod
    def _check_tls(hostname: str) -> str:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    version = ssock.version()
                    return f"Connection established using {version}\nCertificate:\n{cert}"
        except Exception as e:
            return f"TLS Handshake failed: {str(e)}"
    
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, hostname: str, user: User) -> list:
        observations = []
        network_log = TLSScanner._check_tls(hostname)
        
        ev_log = EvidenceService.store_evidence(db, org_id, EvidenceType.NETWORK_LOG, network_log)

        obs_in = ObservationCreate(
            org_id=org_id,
            project_id=project_id,
            asset_id=asset_id,
            observation_type=ObservationType.WEAK_TLS,
            title=f"Potential Weak TLS at {hostname}",
            fingerprint=f"weak_tls_{hostname}"
        )
        obs = ObservationService.create_or_get_observation(db, obs_in, user)
        observations.append((obs, [ev_log]))
        return observations
