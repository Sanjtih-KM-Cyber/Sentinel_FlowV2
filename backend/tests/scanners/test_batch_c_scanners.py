import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType

from app.services.scanners.command_injection_scanner import CommandInjectionScanner
from app.services.scanners.ssti_scanner import SSTIScanner
from app.services.scanners.xxe_scanner import XXEScanner
from app.services.scanners.ssrf_scanner import SSRFScanner
from app.services.scanners.crlf_scanner import CRLFInjectionScanner
from app.services.scanners.host_header_scanner import HostHeaderScanner
from app.services.scanners.path_traversal_scanner import PathTraversalScanner
from app.services.scanners.hardcoded_secret_scanner import HardcodedSecretScanner
from app.services.scanners.sensitive_data_scanner import SensitiveDataExposureScanner
from app.services.scanners.api_endpoint_scanner import ApiEndpointScanner
import httpx
import uuid

class MockResponse:
    def __init__(self, status_code, text, headers=None, url=None):
        self.status_code = status_code
        self.text = text
        self.headers = httpx.Headers(headers or {})
        self.url = httpx.URL(url or "http://test.com")
        self.reason_phrase = "OK" if status_code == 200 else "Found"

@pytest.mark.asyncio
@patch('app.services.tools.commix_integration.CommixIntegration.run_scan')
async def test_command_injection_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4() 
    
    mock_run.return_value = {
        "target": "http://test.com",
        "vulnerable": True,
        "injections": [{"type": "command_injection", "payload": "ping 8.8.8.8", "parameter": "url"}],
        "raw_output": "is vulnerable"
    }
    
    observations = await CommandInjectionScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user, oob_domain="oob.local")
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.COMMAND_INJECTION
    assert len(evs) == 1
    assert "oob_token" in obs.metadata_json

@pytest.mark.asyncio
@patch('app.services.tools.tplmap_integration.TplMapIntegration.run_scan')
async def test_ssti_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "vulnerable": True,
        "engine": "Jinja2",
        "payload": "{{7*7}}",
        "execution_evidence": "49",
        "raw_output": "Jinja2 plugin"
    }
    
    observations = await SSTIScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.SSTI
    assert len(evs) == 1
    assert obs.metadata_json["execution_evidence"] == "49"

@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_xxe_scanner(mock_post, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_post.return_value = MockResponse(200, "OK")
    
    observations = await XXEScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.XXE
    assert len(evs) == 2
    assert "oob_token" in obs.metadata_json

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_ssrf_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "OK")
    
    observations = await SSRFScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.SSRF
    assert len(evs) == 1
    assert "oob_token" in obs.metadata_json

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_crlf_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "OK", {"Set-Cookie": "crlf=injection"})
    
    observations = await CRLFInjectionScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.CRLF_INJECTION
    assert len(evs) == 2

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_host_header_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, '<html><a href="http://evil.example.com/reset">Reset</a></html>', {"Location": "http://evil.example.com/login"})
    
    observations = await HostHeaderScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.HOST_HEADER_INJECTION
    assert len(evs) == 2
    assert obs.metadata_json["reflection_verified"] is True

@pytest.mark.asyncio
@patch('app.services.tools.dotdotpwn_integration.DotDotPwnIntegration.run_scan')
async def test_path_traversal_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "vulnerable": True,
        "payload": "../../../../etc/passwd",
        "raw_output": "LFI",
        "matched_signature": "root:x:0:0"
    }
    
    observations = await PathTraversalScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.PATH_TRAVERSAL
    assert len(evs) == 2

@pytest.mark.asyncio
@patch('app.services.tools.trufflehog_integration.TruffleHogIntegration.run_scan')
async def test_hardcoded_secret_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "secrets": [{"DetectorName": "AWS", "Redacted": "AKIA*****", "File": "app.js", "Line": 42}],
        "raw_output": "found it",
        "error": None
    }
    
    observations = await HardcodedSecretScanner.scan(db_session, org_id, project_id, asset_id, "/src", "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.HARDCODED_SECRET
    assert len(evs) == 1
    assert obs.metadata_json["masked_secret"] == "AKIA*****"

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_sensitive_data_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "Traceback (most recent call last):\n  File \"app.py\", line 12, in <module>\n Exception: Internal IP 10.0.0.52")
    
    observations = await SensitiveDataExposureScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.SENSITIVE_DATA_EXPOSURE
    assert len(obs.metadata_json["exposures"]) >= 2  # stack trace and internal ip

@pytest.mark.asyncio
@patch('app.services.tools.ffuf_integration.FfufIntegration.run_scan')
async def test_api_endpoint_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "endpoints": [{"url": "http://test.com/api/v1/ping", "status": 200}],
        "raw_output": "found /api/v1/ping",
        "error": None
    }
    
    observations = await ApiEndpointScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.API_ENDPOINT
    assert len(obs.metadata_json["endpoints"]) == 1
