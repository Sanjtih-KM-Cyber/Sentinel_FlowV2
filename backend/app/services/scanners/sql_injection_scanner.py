import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.sqlmap_integration import SqlMapIntegration

class SqlInjectionScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        result = await SqlMapIntegration.run_scan(target_url)
        
        injections = result.get("injections", [])
        if injections:
            # Store raw tool output once
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )
            
            # Create a finding per injection type
            for inj in injections:
                inj_type = inj.get("type", "unknown")
                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.SQL_INJECTION,
                    title=f"SQL Injection ({inj_type}) at {target_url}",
                    fingerprint=f"sqli_{inj_type}_{target_url}_{hash(inj.get('payload', ''))}",
                    metadata_json={
                        "vulnerable": True,
                        "injection_type": inj_type,
                        "payload": inj.get("payload"),
                        "dbms": inj.get("dbms")
                    }
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_out]))
        
        return observations
