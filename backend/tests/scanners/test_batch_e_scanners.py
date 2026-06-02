import pytest
import base64
from unittest.mock import patch, MagicMock
from app.models.observation import ObservationType
from app.services.scanners.business_logic_scanner import BusinessLogicScanner
from app.services.scanners.prototype_pollution_scanner import PrototypePollutionScanner
from app.services.scanners.insecure_deserialization_scanner import InsecureDeserializationScanner
from app.services.scanners.subdomain_takeover_scanner import SubdomainTakeoverScanner
from app.models.application_mapping import DiscoveredEndpoint, DiscoveredParameter, Workflow, WorkflowStep

class MockResponse:
    def __init__(self, status_code, text, json_data=None, content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content
        self.reason_phrase = "OK"
        self._json = json_data
        
    def json(self):
         return self._json

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
@patch('httpx.AsyncClient.request')
async def test_business_logic_scanner(mock_req, mock_get, db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user1"]
    
    # State tracking service captures state with GET usually
    mock_get.side_effect = [
        MockResponse(status_code=200, text="", json_data={"status": "pending"}), # before
        MockResponse(status_code=200, text="", json_data={"status": "approved"}) # after
    ]
    
    mock_req.return_value = MockResponse(status_code=200, text="Workflow step successful")
    
    # Needs some workflow setup
    ep = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="POST", url="http://test/checkout", source="test")
    db_session.add(ep)
    wf = Workflow(org_id=org_id, project_id=project_id, name="Test Flow")
    db_session.add(wf)
    db_session.flush()
    ws1 = WorkflowStep(workflow_id=wf.id, step_order=1, endpoint_id=ep.id, action_type="GET")
    ws2 = WorkflowStep(workflow_id=wf.id, step_order=2, endpoint_id=ep.id, action_type="POST")
    db_session.add(ws1)
    db_session.add(ws2)
    db_session.commit()
    
    observations = await BusinessLogicScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.BUSINESS_LOGIC
    assert len(evs) == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient.request')
async def test_prototype_pollution_scanner(mock_req, db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user1"]
    
    mock_req.return_value = MockResponse(status_code=200, text='{"status": "polluted"}')
    
    ep = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="POST", url="http://test/api/config", source="test")
    db_session.add(ep)
    db_session.flush()
    param = DiscoveredParameter(endpoint_id=ep.id, name="theme", param_type="JSON", data_type="string")
    db_session.add(param)
    db_session.commit()
    
    observations = await PrototypePollutionScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.PROTOTYPE_POLLUTION
    assert len(evs) == 2

@pytest.mark.asyncio
@patch('httpx.AsyncClient.request')
async def test_insecure_deserialization_scanner(mock_req, db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user1"]
    
    mock_req.return_value = MockResponse(status_code=200, text='OOB_trigger triggered on backend!')
    
    ep = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="POST", url="http://test/submit", source="test")
    db_session.add(ep)
    db_session.flush()
    param = DiscoveredParameter(endpoint_id=ep.id, name="state", param_type="POST", data_type="string", default_value=base64.b64encode(b"aced...").decode())
    db_session.add(param)
    db_session.commit()
    
    observations = await InsecureDeserializationScanner.scan("http://test", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.INSECURE_DESERIALIZATION
    assert len(evs) == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_subdomain_takeover_scanner(mock_get, db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    user = setup_data["user1"]
    
    mock_get.return_value = MockResponse(status_code=404, text="", content=b"<title>NoSuchBucket</title>")
    
    # We pass 'http://example.com' to trigger the subfinder mock finding 'old-s3.example.com'
    observations = await SubdomainTakeoverScanner.scan("http://example.com", db_session, org_id, project_id, user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.SUBDOMAIN_TAKEOVER
    assert len(evs) == 3
