import pytest
from app.models.observation import ObservationType, Observation
from app.models.evidence import EvidenceType, Evidence
from app.services.rules.vulnerability_rules import (
    LdapInjectionRule,
    XPathInjectionRule,
    GraphqlSecurityRule,
    DefaultCredentialsRule,
    MassAssignmentRule,
    IdorRule,
    CsrfRule,
    AuthenticationBypassRule
)

@pytest.mark.asyncio
async def test_ldap_rule(db_session):
    rule = LdapInjectionRule()
    
    obs = Observation(observation_type=ObservationType.LDAP_INJECTION, metadata_json={"vuln_type": "error"})
    ev = Evidence(evidence_type=EvidenceType.RESPONSE, snippet="NamingException occurred")
    
    assert await rule.verify(db_session, obs, [ev])

@pytest.mark.asyncio
async def test_xpath_rule(db_session):
    rule = XPathInjectionRule()
    
    obs = Observation(observation_type=ObservationType.XPATH_INJECTION, metadata_json={"vuln_type": "error"})
    ev = Evidence(evidence_type=EvidenceType.RESPONSE, snippet="XPathException in query")
    
    assert await rule.verify(db_session, obs, [ev])

@pytest.mark.asyncio
async def test_graphql_rule(db_session):
    rule = GraphqlSecurityRule()
    obs = Observation(observation_type=ObservationType.GRAPHQL_SECURITY, metadata_json={"is_vulnerable": True})
    assert await rule.verify(db_session, obs, [])

@pytest.mark.asyncio
async def test_default_credentials_rule(db_session):
    rule = DefaultCredentialsRule()
    obs = Observation(observation_type=ObservationType.DEFAULT_CREDENTIALS, metadata_json={"authenticated": True})
    
    # Needs at least 3 pieces of evidence
    evs = [
        Evidence(evidence_type=EvidenceType.REQUEST, snippet="req"),
        Evidence(evidence_type=EvidenceType.RESPONSE, snippet="res"),
        Evidence(evidence_type=EvidenceType.RESPONSE, snippet="val")
    ]
    assert await rule.verify(db_session, obs, evs)

@pytest.mark.asyncio
async def test_mass_assignment_rule(db_session):
    rule = MassAssignmentRule()
    obs = Observation(observation_type=ObservationType.MASS_ASSIGNMENT, metadata_json={"state_mutated": True})
    evs = [
        Evidence(evidence_type=EvidenceType.REQUEST, snippet="req"),
        Evidence(evidence_type=EvidenceType.RESPONSE, snippet="res"),
        Evidence(evidence_type=EvidenceType.RESPONSE, snippet="state")
    ]
    assert await rule.verify(db_session, obs, evs)

@pytest.mark.asyncio
async def test_idor_rule(db_session):
    rule = IdorRule()
    obs = Observation(observation_type=ObservationType.IDOR, metadata_json={"cross_user_access": True})
    assert await rule.verify(db_session, obs, [])

@pytest.mark.asyncio
async def test_csrf_rule(db_session):
    rule = CsrfRule()
    obs = Observation(observation_type=ObservationType.CSRF, metadata_json={"action_succeeded": True, "missing_token": True})
    assert await rule.verify(db_session, obs, [])

@pytest.mark.asyncio
async def test_authentication_bypass_rule(db_session):
    rule = AuthenticationBypassRule()
    obs = Observation(observation_type=ObservationType.AUTHENTICATION_BYPASS, metadata_json={"bypassed": True})
    assert await rule.verify(db_session, obs, [])
