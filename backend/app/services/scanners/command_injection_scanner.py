import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService
from app.services.tools.commix_integration import CommixIntegration
from app.schemas.interaction import InteractionTokenCreate
from app.services.interaction_service import InteractionService
from app.core.config import settings

class CommandInjectionScanner:
    @staticmethod
    async def scan(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, asset_id: uuid.UUID, target_url: str, user: User, oob_domain: str = None) -> list:
        observations = []
        
        # Generate an actual OOB token
        token_in = InteractionTokenCreate(org_id=org_id, project_id=project_id, source_module="COMMAND_INJECTION")
        db_token = InteractionService.generate_token(db, token_in)
        
        # Use a realistic OOB payload URL structure based on config or default localhost
        base_domain = settings.OOB_DOMAIN if hasattr(settings, "OOB_DOMAIN") else "localhost:3000/api/oob"
        interaction_url = f"http://{base_domain}/{db_token.token}"
        
        # In a real tool integration, we give this payload to the tool
        # Commix handles this via param but here we simulate it via params
        payload_param = f"curl+-s+{interaction_url}"
        
        result = await CommixIntegration.run_scan(target_url, params=payload_param)
        injections = result.get("injections", [])
        
        if injections:
            ev_out = EvidenceService.store_evidence(
                db, 
                org_id, 
                EvidenceType.TOOL_OUTPUT, 
                result.get("raw_output", "")
            )
            
            for inj in injections:
                obs_in = ObservationCreate(
                    org_id=org_id,
                    project_id=project_id,
                    asset_id=asset_id,
                    observation_type=ObservationType.COMMAND_INJECTION,
                    title=f"Command Injection at {target_url}",
                    fingerprint=f"cmdi_{target_url}_{hash(inj.get('payload'))}",
                    metadata_json={
                        "vulnerable": True,
                        "injection_type": inj.get("type"),
                        "payload": inj.get("payload"),
                        "parameter": inj.get("parameter"),
                        "oob_token": db_token.token
                    }
                )
                obs = ObservationService.create_or_get_observation(db, obs_in, user)
                observations.append((obs, [ev_out]))
        
        return observations

