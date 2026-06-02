import pytest
from unittest.mock import patch, MagicMock
from app.models.observation import ObservationType
from app.services.scanners.ldap_scanner import LDAPInjectionScanner
from app.services.scanners.xpath_scanner import XPathInjectionScanner
from app.services.scanners.graphql_scanner import GraphQLSecurityScanner
from app.services.scanners.default_credentials_scanner import DefaultCredentialsScanner
from app.services.scanners.mass_assignment_scanner import MassAssignmentScanner
from app.services.scanners.idor_scanner import IDORScanner
from app.services.scanners.csrf_scanner import CSRFScanner
from app.services.scanners.authentication_bypass_scanner import AuthenticationBypassScanner
import httpx

class MockResponse:
    def __init__(self, status_code, text, json_data=None, cookies=None, headers=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data or {}
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.reason_phrase = "OK"
        
    def json(self):
        return self._json


@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_ldap_scanner(mock_post, db_session, setup_data):
    mock_post.return_value = MockResponse(status_code=500, text="NamingException occurred")
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await LDAPInjectionScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.LDAP_INJECTION
    assert len(evs) == 2


@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_xpath_scanner(mock_post, db_session, setup_data):
    mock_post.return_value = MockResponse(status_code=500, text="XPathException in query")
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await XPathInjectionScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.XPATH_INJECTION
    assert len(evs) == 2


@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
@patch('httpx.AsyncClient.get')
async def test_graphql_scanner(mock_get, mock_post, db_session, setup_data):
    mock_get.return_value = MockResponse(status_code=200, text="fetch('/api/graphql');")
    mock_post.side_effect = [
        MockResponse(status_code=200, text='{"data":{"__schema":{}}}', json_data={"data":{"__schema":{}}}),
        MockResponse(status_code=200, text='{"data":{"user":{}}}', json_data={"data":{"user":{}}})  # No errors dict
    ]
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await GraphQLSecurityScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 2
    assert any(o[0].metadata_json["issue_type"] == "introspection" for o in observations)
    assert any(o[0].metadata_json["issue_type"] == "complexity" for o in observations)


@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_default_creds_scanner(mock_post, db_session, setup_data):
    mock_post.return_value = MockResponse(status_code=200, text="valid token", cookies={"session": "123"})
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await DefaultCredentialsScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.DEFAULT_CREDENTIALS
    assert len(evs) == 3


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
@patch('httpx.AsyncClient.put')
async def test_mass_assignment_scanner(mock_put, mock_get, db_session, setup_data):
    # State tracking service captures state with GET
    mock_get.side_effect = [
        MockResponse(status_code=200, text="", json_data={"is_admin": False}),
        MockResponse(status_code=200, text="", json_data={"is_admin": True})
    ]
    mock_put.return_value = MockResponse(status_code=200, text="updated")
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await MassAssignmentScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.MASS_ASSIGNMENT
    assert len(evs) == 3


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_idor_scanner(mock_get, db_session, setup_data):
    # First get is object mapping (gets objects)
    # Second get is accessing target obj
    mock_get.side_effect = [
        MockResponse(status_code=200, text='{"user_id": 42}'),
        MockResponse(status_code=200, text="Private Document for UserA accessed by UserB")
    ]
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await IDORScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.IDOR
    assert len(evs) == 2


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
@patch('httpx.AsyncClient.post')
async def test_csrf_scanner(mock_post, mock_get, db_session, setup_data):
    # get 1: /settings (forms)
    # get 2: capture state before
    # get 3: capture state after
    mock_get.side_effect = [
        MockResponse(status_code=200, text='<form action="/test" method="POST"><input type="hidden" name="csrf" value="123"></form>'),
        MockResponse(status_code=200, text='{"updated": false}', json_data={"updated": False}),
        MockResponse(status_code=200, text='{"updated": true}', json_data={"updated": True})
    ]
    
    mock_post.return_value = MockResponse(status_code=200, text="Email updated")
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await CSRFScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.CSRF
    assert len(evs) == 2


@pytest.mark.asyncio
@patch('httpx.AsyncClient.request')
async def test_auth_bypass_scanner(mock_req, db_session, setup_data):
    # anon request & admin request for each endpoint (total 4 tests if 2 eps)
    mock_req.side_effect = [
        MockResponse(status_code=200, text="Admin Dashboard contents accessed anonymously"),
        MockResponse(status_code=200, text="Admin Dashboard contents accessed by admin"),
        MockResponse(status_code=200, text="Admin Users accessed anonymously"),
        MockResponse(status_code=200, text="Admin Users accessed by admin")
    ]
    
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user"]
    
    observations = await AuthenticationBypassScanner.scan("http://test", db_session, org_id, project_id, user)
    
    # 1 for each endpoint tested = 2 total
    assert len(observations) == 2
    for o in observations:
        obs, evs = o
        assert obs.observation_type == ObservationType.AUTHENTICATION_BYPASS
        assert len(evs) == 2
