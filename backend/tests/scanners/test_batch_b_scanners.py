import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.services.scanners.sql_injection_scanner import SqlInjectionScanner
from app.services.scanners.xss_scanner import XSSScanner
from app.services.scanners.http_method_scanner import HttpMethodScanner
from app.services.scanners.waf_scanner import WafScanner
from app.services.scanners.port_scanner import PortDiscoveryScanner
from app.services.scanners.tech_fingerprint_scanner import TechFingerprintScanner
from app.services.scanners.clickjacking_scanner import ClickjackingScanner
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
@patch('app.services.tools.sqlmap_integration.SqlMapIntegration.run_scan')
async def test_sql_injection_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4() 
    
    mock_run.return_value = {
        "target": "http://test.com",
        "vulnerable": True,
        "injections": [{"type": "error-based", "payload": "1'", "dbms": "MySQL"}],
        "raw_output": "is vulnerable",
        "error": None
    }
    
    observations = await SqlInjectionScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.SQL_INJECTION
    assert len(evs) == 1
    assert evs[0].evidence_type == EvidenceType.TOOL_OUTPUT

@pytest.mark.asyncio
@patch('app.services.tools.dalfox_integration.DalfoxIntegration.run_scan')
async def test_xss_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "vulnerable": True,
        "raw_output": "XSS Found",
        "findings": [{"payload": "<script>", "reflection_context": "body", "execution_evidence": "alert", "method": "GET"}],
        "error": None
    }
    
    observations = await XSSScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    # 3 modes tested: GET, POST form, POST JSON. All hit the same mock.
    assert len(observations) == 3
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.CROSS_SITE_SCRIPTING
    assert len(evs) == 1
    assert evs[0].evidence_type == EvidenceType.TOOL_OUTPUT

@pytest.mark.asyncio
@patch('httpx.AsyncClient.request')
async def test_http_method_scanner(mock_request, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_request.return_value = MockResponse(200, "TRACE / HTTP/1.1")
    
    observations = await HttpMethodScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 2  # TRACE and TRACK
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.HTTP_TRACE_ENABLED

@pytest.mark.asyncio
@patch('app.services.tools.wafw00f_integration.Wafw00fIntegration.run_scan')
async def test_waf_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "detected": True,
        "vendor": "Cloudflare",
        "confidence": 0.95,
        "raw_output": "is behind Cloudflare WAF"
    }
    
    observations = await WafScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.WAF_DETECTED

@pytest.mark.asyncio
@patch('app.services.tools.nmap_integration.NmapIntegration.run_scan')
async def test_port_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "test.com",
        "open_ports": [{"port": 80, "protocol": "tcp", "service": "http"}],
        "raw_output": "80/tcp open"
    }
    
    observations = await PortDiscoveryScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.OPEN_PORT

@pytest.mark.asyncio
@patch('app.services.tools.wappalyzer_integration.WappalyzerIntegration.run_scan')
async def test_tech_fingerprint_scanner(mock_run, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_run.return_value = {
        "target": "http://test.com",
        "technologies": [{"name": "React", "confidence": 100, "categories": ["UI"], "version": "17"}],
        "raw_output": "stuff"
    }
    
    observations = await TechFingerprintScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.TECHNOLOGY_FINGERPRINT
    assert obs.metadata_json["name"] == "React"

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_clickjacking_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "<html><form><input type='submit'></form></html>")
    
    observations = await ClickjackingScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.CLICKJACKING
    assert obs.metadata_json["missing_protection"] == True
    assert obs.metadata_json["is_state_changing"] == True

