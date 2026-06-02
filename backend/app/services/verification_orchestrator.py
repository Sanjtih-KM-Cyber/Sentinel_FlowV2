import uuid
import datetime
from sqlalchemy.orm import Session
from fastapi import Request
from typing import List, Optional
from app.models.verification_run import VerificationRun, VerificationStatus
from app.models.observation import Observation
from app.models.user import User
from app.models.evidence import Evidence
from app.services.verification_framework import BaseVerificationRule
from app.services.audit_service import log_audit_event
from app.schemas.observation_finding import VerificationRunCreate
from app.services.confidence_service import ConfidenceService
from app.services.rules.vulnerability_rules import (
    SensitiveFileExposureRule,
    InsecureCookieRule,
    WeakSecurityHeaderRule,
    WeakTLSRule,
    AdminPanelExposureRule,
    OpenRedirectRule,
    CORSMisconfigRule,
    JWTSecurityRule,
    SqlInjectionRule,
    CrossSiteScriptingRule,
    HttpMethodTraceRule,
    WafDetectionRule,
    ClickjackingRule,
    CommandInjectionRule,
    SstiRule,
    XxeRule,
    SsrfRule,
    CrlfInjectionRule,
    HostHeaderInjectionRule,
    PathTraversalRule,
    HardcodedSecretRule,
    SensitiveDataExposureRule,
    LdapInjectionRule,
    XPathInjectionRule,
    GraphqlSecurityRule,
    DefaultCredentialsRule,
    MassAssignmentRule,
    IdorRule,
    CsrfRule,
    AuthenticationBypassRule
)

# Registry of all known rules
DEFAULT_RULES = [
    SensitiveFileExposureRule(),
    InsecureCookieRule(),
    WeakSecurityHeaderRule(),
    WeakTLSRule(),
    AdminPanelExposureRule(),
    OpenRedirectRule(),
    CORSMisconfigRule(),
    JWTSecurityRule(),
    SqlInjectionRule(),
    CrossSiteScriptingRule(),
    HttpMethodTraceRule(),
    WafDetectionRule(),
    ClickjackingRule(),
    CommandInjectionRule(),
    SstiRule(),
    XxeRule(),
    SsrfRule(),
    CrlfInjectionRule(),
    HostHeaderInjectionRule(),
    PathTraversalRule(),
    HardcodedSecretRule(),
    SensitiveDataExposureRule(),
    LdapInjectionRule(),
    XPathInjectionRule(),
    GraphqlSecurityRule(),
    DefaultCredentialsRule(),
    MassAssignmentRule(),
    IdorRule(),
    CsrfRule(),
    AuthenticationBypassRule()
]

class VerificationService:
    def __init__(self, rules: List[BaseVerificationRule] = None):
        self.rules = rules if rules is not None else DEFAULT_RULES

    def get_rules_for_observation(self, observation: Observation) -> List[BaseVerificationRule]:
        return [rule for rule in self.rules if observation.observation_type in rule.observation_criteria()]

    async def execute_verification(
        self, 
        db: Session, 
        observation: Observation, 
        evidence_list: List[Evidence], 
        user: User, 
        request: Request = None
    ):
        matching_rules = self.get_rules_for_observation(observation)
        for rule in matching_rules:
            # Create VerificationRun
            run = VerificationRun(
                org_id=observation.org_id,
                observation_id=observation.id,
                rule_id=rule.rule_id,
                status=VerificationStatus.RUNNING,
                started_at=datetime.datetime.utcnow()
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            # Audit event: verification.started
            log_audit_event(
                db=db,
                org_id=run.org_id,
                user=user,
                action="verification.started",
                resource_type="verification_run",
                resource_id=str(run.id),
                request=request
            )

            try:
                # Check evidence requirements
                provided_evidence_types = {e.evidence_type for e in evidence_list}
                required_evidence_types = set(rule.evidence_requirements())
                
                if not required_evidence_types.issubset(provided_evidence_types):
                    raise ValueError(f"Missing required evidence types: {required_evidence_types - provided_evidence_types}")

                # Verify
                is_verified = await rule.verify(db, observation, evidence_list)
                
                if is_verified:
                    from app.services.finding_service import FindingService
                    from app.schemas.observation_finding import FindingCreate, FindingStatus
                    from app.models.finding import Severity
                    
                    finding_in = FindingCreate(
                        org_id=observation.org_id,
                        project_id=observation.project_id,
                        asset_id=observation.asset_id,
                        observation_id=observation.id,
                        title=f"Verified finding for {rule.rule_id}",
                        status=FindingStatus.POTENTIAL, # or VERIFIED
                        severity=Severity.MEDIUM # default, maybe rule provides this?
                    )
                    finding = FindingService.create_finding(db, finding_in, user, request)
                    FindingService.update_finding_status(db, observation.org_id, finding.id, FindingStatus.VERIFIED, user, request)
                    
                    # Confidence calculation
                    confidence_score_base = rule.calculate_confidence(observation, evidence_list, is_verified)
                    from app.schemas.observation_finding import ConfidenceScoreCreate
                    
                    confidence_score_in = ConfidenceScoreCreate(
                        level=confidence_score_base.level,
                        score_numerical=confidence_score_base.score_numerical,
                        reasoning=confidence_score_base.reasoning,
                        finding_id=finding.id,
                        org_id=finding.org_id
                    )
                    
                    ConfidenceService.add_confidence_score(db, confidence_score_in)
                    
                run.status = VerificationStatus.COMPLETED
                
            except Exception as e:
                run.status = VerificationStatus.FAILED
                run.error_message = str(e)
                
            run.completed_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(run)

            # Audit event: verification.completed
            log_audit_event(
                db=db,
                org_id=run.org_id,
                user=user,
                action="verification.completed",
                resource_type="verification_run",
                resource_id=str(run.id),
                request=request
            )
