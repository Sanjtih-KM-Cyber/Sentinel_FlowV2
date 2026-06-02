import pytest
from unittest.mock import patch, MagicMock
from app.services.verification_service import VerificationService
import httpx
import dns.asyncresolver
import dns.exception

@pytest.mark.asyncio
@patch('dns.asyncresolver.resolve')
async def test_dns_txt_success(mock_resolve):
    mock_answer = MagicMock()
    mock_rdata = MagicMock()
    mock_rdata.strings = [b'aegis-testtoken']
    mock_answer.__iter__.return_value = [mock_rdata]
    mock_resolve.return_value = mock_answer
    
    success, msg = await VerificationService.verify_dns_txt('example.com', 'aegis-testtoken')
    assert success is True
    assert msg is None

@pytest.mark.asyncio
@patch('dns.asyncresolver.resolve')
async def test_dns_txt_failure_no_match(mock_resolve):
    mock_answer = MagicMock()
    mock_rdata = MagicMock()
    mock_rdata.strings = [b'aegis-wrongtoken']
    mock_answer.__iter__.return_value = [mock_rdata]
    mock_resolve.return_value = mock_answer
    
    success, msg = await VerificationService.verify_dns_txt('example.com', 'aegis-testtoken')
    assert success is False
    assert msg is not None

@pytest.mark.asyncio
@patch('dns.asyncresolver.resolve', side_effect=dns.resolver.NXDOMAIN)
async def test_dns_txt_failure_nxdomain(mock_resolve):
    success, msg = await VerificationService.verify_dns_txt('example.com', 'aegis-testtoken')
    assert success is False
    assert "DNS domain does not exist" in msg

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.get')
async def test_html_verification_success(mock_get, mock_validate):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'aegis-testtoken'
    mock_get.return_value = mock_response
    
    success, msg = await VerificationService.verify_html_file('example.com', 'aegis-testtoken')
    assert success is True
    assert msg is None

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.get')
async def test_html_verification_failure_wrong_content(mock_get, mock_validate):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'wrong'
    mock_get.return_value = mock_response
    
    success, msg = await VerificationService.verify_html_file('example.com', 'aegis-testtoken')
    assert success is False
    assert msg is not None

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.get', side_effect=httpx.TimeoutException("Timeout"))
async def test_html_verification_failure_timeout(mock_get, mock_validate):
    success, msg = await VerificationService.verify_html_file('example.com', 'aegis-testtoken')
    assert success is False
    assert "timed out" in msg

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.get')
async def test_meta_verification_success(mock_get, mock_validate):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<html><head><meta name="aegis-verification" content="aegis-testtoken"></head></html>'
    mock_get.return_value = mock_response
    
    success, msg = await VerificationService.verify_meta_tag('example.com', 'aegis-testtoken')
    assert success is True
    assert msg is None

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.get')
async def test_meta_verification_failure_no_tag(mock_get, mock_validate):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<html><head></head></html>'
    mock_get.return_value = mock_response
    
    success, msg = await VerificationService.verify_meta_tag('example.com', 'aegis-testtoken')
    assert success is False
    assert msg is not None

@pytest.mark.asyncio
@patch('socket.gethostbyname')
async def test_ssrf_localhost_block(mock_gethostbyname):
    mock_gethostbyname.return_value = '127.0.0.1'
    # Test valid target URL function directly
    is_valid = VerificationService.validate_target_url('http://localhost')
    assert is_valid is False
    
    # Try through html file method, should short-circuit
    success, msg = await VerificationService.verify_html_file('localhost', 'aegis-testtoken')
    assert success is False
    assert "prohibited IP address" in msg

@pytest.mark.asyncio
@patch('socket.gethostbyname')
async def test_ssrf_private_ip_block(mock_gethostbyname):
    mock_gethostbyname.return_value = '192.168.1.100'
    is_valid = VerificationService.validate_target_url('http://internal.example.com')
    assert is_valid is False
    
    success, msg = await VerificationService.verify_html_file('internal.example.com', 'aegis-testtoken')
    assert success is False
    assert "prohibited IP address" in msg

@pytest.mark.asyncio
@patch('socket.gethostbyname')
async def test_ssrf_link_local_block(mock_gethostbyname):
    mock_gethostbyname.return_value = '169.254.169.254'
    is_valid = VerificationService.validate_target_url('http://169.254.169.254')
    assert is_valid is False

@pytest.mark.asyncio
@patch('socket.gethostbyname')
async def test_valid_public_ip(mock_gethostbyname):
    mock_gethostbyname.return_value = '8.8.8.8'
    is_valid = VerificationService.validate_target_url('http://google.com')
    assert is_valid is True
