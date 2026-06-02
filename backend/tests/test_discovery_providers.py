import pytest
from app.services.discovery_providers import SubdomainProviderCRTsh, DnsIntelligenceProvider, HttpProbingProvider, TechnologyFingerprintService
from unittest.mock import patch, MagicMock
import httpx

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_subdomain_provider_crt_sh_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name_value": "sub1.example.com"},
        {"name_value": "sub2.example.com\\nsub3.example.com"}
    ]
    mock_get.return_value = mock_response

    subdomains = await SubdomainProviderCRTsh.discover("example.com")
    assert len(subdomains) == 3
    assert "sub1.example.com" in subdomains
    assert "sub2.example.com" in subdomains
    assert "sub3.example.com" in subdomains

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_subdomain_provider_crt_sh_retry_on_503(mock_get):
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 503
    
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = [{"name_value": "sub1.example.com"}]
    
    mock_get.side_effect = [mock_response_1, mock_response_2]

    subdomains = await SubdomainProviderCRTsh.discover("example.com")
    assert len(subdomains) == 1
    assert mock_get.call_count == 2

@pytest.mark.asyncio
@patch('dns.asyncresolver.resolve')
async def test_dns_intelligence_provider(mock_resolve):
    mock_answer = MagicMock()
    mock_answer.__iter__.return_value = [MagicMock(__str__=lambda x: "192.168.1.1")]
    mock_resolve.return_value = mock_answer
    
    results = await DnsIntelligenceProvider.collect("example.com")
    # By default it checks 6 types, they all return 192.168.1.1 in this mock
    assert "A" in results
    assert results["A"] == ["192.168.1.1"]

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.stream')
async def test_http_probing_provider_stream(mock_stream, mock_validate):
    class AsyncIterBytes:
        async def __aiter__(self):
            yield b'<html><title>Test</title></html>'
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'text/html', 'server': 'nginx'}
    mock_response.url = "http://example.com"
    mock_response.aiter_bytes = AsyncIterBytes
    
    # Context manager setup
    mock_cm = MagicMock()
    mock_cm.__aenter__.return_value = mock_response
    mock_stream.return_value = mock_cm

    results = await HttpProbingProvider.probe("example.com")
    assert len(results) == 2  # http and https
    assert results[0]["title"] == "Test"
    assert results[0]["server_header"] == "nginx"
    assert results[0]["status_code"] == 200

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=False)
@patch('httpx.AsyncClient.stream')
async def test_http_probing_ssrf_block(mock_stream, mock_validate):
    results = await HttpProbingProvider.probe("169.254.169.254")
    assert len(results) == 0
    mock_stream.assert_not_called()

@pytest.mark.asyncio
@patch('app.services.verification_service.VerificationService.validate_target_url', return_value=True)
@patch('httpx.AsyncClient.stream')
async def test_http_probing_large_response(mock_stream, mock_validate):
    class AsyncIterBytes:
        async def __aiter__(self):
            # Yield chunks that exceed 100KB
            yield b'A' * 50000
            yield b'B' * 60000
            yield b'C' * 10000 # Should not be reached/added fully
            
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'text/plain'}
    mock_response.url = "http://example.com"
    mock_response.aiter_bytes = AsyncIterBytes
    
    mock_cm = MagicMock()
    mock_cm.__aenter__.return_value = mock_response
    mock_stream.return_value = mock_cm

    results = await HttpProbingProvider.probe("example.com")
    assert len(results) == 2
    # Total length should be exactly 110000 bytes since it breaks after the second chunk
    assert results[0]["content_length"] == 110000

@pytest.mark.asyncio
@patch('dns.asyncresolver.Resolver.resolve')
async def test_dns_intelligence_timeout(mock_resolve):
    import dns.exception
    mock_resolve.side_effect = dns.exception.Timeout
    
    results = await DnsIntelligenceProvider.collect("example.com")
    # All types should fail due to timeout and return empty arrays
    for k, v in results.items():
        assert len(v) == 0

def test_technology_fingerprint_service():
    probe_data = {
        "headers": {
            "server": "nginx/1.18.0",
            "x-powered-by": "PHP/7.4.3"
        },
        "server_header": "nginx/1.18.0"
    }
    fps = TechnologyFingerprintService.extract_fingerprints(probe_data)
    
    names = [f["name"] for f in fps]
    assert "Nginx" in names
    assert "PHP" in names
    
    for f in fps:
        if f["name"] == "Nginx":
            assert f["version"] == "1.18.0"
        if f["name"] == "PHP":
            assert f["version"] == "7.4.3"
