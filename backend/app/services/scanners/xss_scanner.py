import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.dalfox_integration import DalfoxIntegration

class XSSScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User) -> list:
        observations = []
        
        modes = [
            {"mode": "GET", "data": None, "headers": None},
            {"mode": "POST", "data": "param=test", "headers": "Content-Type: application/x-www-form-urlencoded"},
            {"mode": "POST", "data": '{"param":"test"}', "headers": "Content-Type: application/json"}
        ]
        
        for m in modes:
            result = await DalfoxIntegration.run_scan(target_url, mode=m["mode"], data=m["data"], headers=m["headers"])
            
            findings = result.get("findings", [])
            if findings:
                ev_out = EvidenceService.store_evidence(
                    db, 
                    org_id, 
                    EvidenceType.TOOL_OUTPUT, 
                    result.get("raw_output", "")
                )
                
                for finding in findings:
                    obs_in = ObservationCreate(
                        org_id=org_id,
                        project_id=project_id,
                        asset_id=asset_id,
                        observation_type=ObservationType.CROSS_SITE_SCRIPTING,
                        title=f"XSS ({m['mode']}) Analysis at {target_url}",
                        fingerprint=f"xss_{m['mode']}_{target_url}_{hash(finding.get('payload'))}",
                        metadata_json={
                            "vulnerable": True,
                            "payload": finding.get("payload"),
                            "reflection_context": finding.get("reflection_context"),
                            "execution_evidence": finding.get("execution_evidence"),
                            "mode": finding.get("method")
                        }
                    )
                    obs = ObservationService.create_or_get_observation(db, obs_in, user)
                    observations.append((obs, [ev_out]))
        
        return observations
