import uuid
import json
import httpx
from typing import List, Tuple, Any
from sqlalchemy.orm import Session
from app.models.observation import ObservationType, Observation
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService, EvidenceType
from app.services.mapping_services import AuthorizationContextService, StateTrackingService
from app.models.application_mapping import Workflow, WorkflowStep
from app.models.user import User

class BusinessLogicScanner:
    @staticmethod
    async def scan(
        target_url: str,
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user: User
    ) -> List[Tuple[Observation, List[Any]]]:
        observations = []
        
        # Discover workflows from the mapping engine
        workflows = db.query(Workflow).filter_by(org_id=org_id, project_id=project_id).all()
        if not workflows:
            return []
            
        ctx_user = AuthorizationContextService.get_context(db, org_id, project_id, "UserA")
        if not ctx_user:
             return []
        
        async with httpx.AsyncClient(verify=False, timeout=10.0, follow_redirects=True) as client:
            for workflow in workflows:
                steps = sorted(workflow.steps, key=lambda s: s.step_order)
                if len(steps) < 2:
                    continue
                
                # Workflow graph analysis: track required transitions
                # We simulate trying to execute a step without its required predecessor
                for idx, step in enumerate(steps):
                    if idx == 0:
                        continue # Can't bypass initialization step
                    
                    target_step = step
                    
                    try:
                        ep = target_step.endpoint
                        
                        # Expected State before manipulation
                        state_before = await StateTrackingService.capture_state(client, ep.url)
                        
                        # Workflow Manipulation: Call the step directly, breaking the transition graph
                        payload = target_step.payload or {}
                        headers = ctx_user.headers or {}
                        
                        if ep.method.upper() in ["POST", "PUT", "PATCH"]:
                            res_mut = await client.request(ep.method, ep.url, json=payload, headers=headers)
                        else:
                            res_mut = await client.request(ep.method, ep.url, headers=headers)
                            
                        # Actual State after manipulation
                        state_after = await StateTrackingService.capture_state(client, ep.url)
                        
                        diff = StateTrackingService.generate_diff(state_before, state_after)
                        state_mutated = bool(diff.get("added") or diff.get("changed") or diff.get("removed"))
                        
                        # Transition validation fails if we can skip predecessor steps and still mutate state
                        if res_mut.status_code in [200, 201] and state_mutated:
                            req_snippet = f"{ep.method} {ep.url}\n{json.dumps(payload)}"
                            res_snippet = f"HTTP/1.1 {res_mut.status_code} {res_mut.reason_phrase}\n{res_mut.text[:200]}"
                            state_snippet = f"Diff: {json.dumps(diff)}"
                            
                            ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                            ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                            ev_state = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, state_snippet)

                            obs_in = ObservationCreate(
                                org_id=org_id,
                                project_id=project_id,
                                observation_type=ObservationType.BUSINESS_LOGIC,
                                title=f"Business Logic Bypass in Workflow: {workflow.name}, Step: {target_step.step_order}",
                                fingerprint=f"business_logic_bypass_{workflow.id}_{target_step.id}",
                                metadata_json={
                                    "workflow": workflow.name,
                                    "bypassed_dependent_step": target_step.endpoint.url,
                                    "state_mutated": True,
                                    "diff": diff
                                }
                            )
                            obs = ObservationService.create_or_get_observation(db, obs_in, user)
                            observations.append((obs, [ev_req, ev_res, ev_state]))
                            
                            break # Found vulnerability in this workflow, move to next
                            
                    except httpx.RequestError:
                        continue
                        
        return observations
