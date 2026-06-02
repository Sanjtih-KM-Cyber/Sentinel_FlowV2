import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from app.models.observation import ObservationType
from app.models.evidence import EvidenceType
from app.services.scanners.sensitive_file_scanner import SensitiveFileScanner
from app.services.scanners.cookie_scanner import CookieObservationService
from app.services.scanners.security_headers_scanner import SecurityHeaderObservationService
from app.services.scanners.tls_scanner import TLSScanner
from app.services.scanners.admin_panel_scanner import AdminPanelScanner
from app.services.scanners.open_redirect_scanner import OpenRedirectScanner
from app.services.scanners.cors_scanner import CORSScanner
from app.services.scanners.jwt_scanner import JWTScanner
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
@patch('httpx.AsyncClient.get')
async def test_sensitive_file_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    # dummy asset id
    asset_id = uuid.uuid4() 
    
    mock_get.return_value = MockResponse(200, "DB_PASSWORD=secret")
    
    observations = await SensitiveFileScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == len(SensitiveFileScanner.TARGET_PATHS)
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.EXPOSED_FILE
    assert len(evs) == 2

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_cookie_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "Hello", {"set-cookie": "session=123; path=/"})
    
    observations = await CookieObservationService.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.INSECURE_COOKIE

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_security_headers_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "Hello", {"Server": "nginx"})
    
    observations = await SecurityHeaderObservationService.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.WEAK_HEADER

@pytest.mark.asyncio
@patch('app.services.scanners.tls_scanner.TLSScanner._check_tls')
async def test_tls_scanner(mock_check_tls, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_check_tls.return_value = "Connection established using TLS 1.0\nCertificate: ..."
    
    observations = await TLSScanner.scan(db_session, org_id, project_id, asset_id, "test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.WEAK_TLS

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_admin_panel_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "Welcome to Admin Dashboard")
    
    observations = await AdminPanelScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == len(AdminPanelScanner.TARGET_PATHS)
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.ADMIN_PANEL

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_open_redirect_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(302, "", {"Location": "http://evil.com"})
    
    observations = await OpenRedirectScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == len(OpenRedirectScanner.PAYLOADS)
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.OPEN_REDIRECT

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_cors_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "{}", {"Access-Control-Allow-Origin": "*"})
    
    observations = await CORSScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.CORS_MISCONFIG

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_jwt_scanner(mock_get, db_session: Session, setup_data: dict):
    user = setup_data["admin1"]
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    asset_id = uuid.uuid4()
    
    mock_get.return_value = MockResponse(200, "{}")
    
    observations = await JWTScanner.scan(db_session, org_id, project_id, asset_id, "http://test.com", user)
    
    assert len(observations) == 1
    obs, evs = observations[0]
    assert obs.observation_type == ObservationType.JWT_ISSUE
