import httpx
from typing import List
from bs4 import BeautifulSoup
import dns.asyncresolver
import dns.exception
import asyncio
import logging
from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)

class SubdomainProviderCRTsh:
    """Subdomain discovery using crt.sh"""
    
    @staticmethod
    async def discover(domain: str) -> List[str]:
        subdomains = set()
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(f"https://crt.sh/?q=%.{domain}&output=json")
                    if response.status_code == 200:
                        data = response.json()
                        for entry in data:
                            name_value = entry.get('name_value', '')
                            for name in name_value.split('\n'):
                                name = name.strip().lower()
                                if name.endswith(domain) and not name.startswith('*'):
                                    subdomains.add(name)
                        break
                    elif response.status_code == 503:
                        logger.warning(f"CRT.sh returned 503 for {domain}, attempt {attempt + 1}")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        logger.warning(f"CRT.sh returned {response.status_code} for {domain}")
                        break
            except (httpx.TimeoutException, httpx.RequestError) as e:
                logger.warning(f"CRT.sh request error for {domain}: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        return list(subdomains)

class DnsIntelligenceProvider:
    """DNS Collection"""
    
    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS']
    
    @staticmethod
    async def collect(domain: str) -> dict:
        results = {}
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 10.0
        for rtype in DnsIntelligenceProvider.RECORD_TYPES:
            try:
                answers = await resolver.resolve(domain, rtype)
                results[rtype] = [str(rdata) for rdata in answers]
            except dns.exception.DNSException as e:
                logger.debug(f"DNS resolve error for {domain} ({rtype}): {str(e)}")
                continue
        return results

class HttpProbingProvider:
    """HTTP Probing"""
    
    @staticmethod
    async def probe(domain: str) -> dict:
        urls = [f"http://{domain}", f"https://{domain}"]
        results = []
        for url in urls:
            if not VerificationService.validate_target_url(url):
                logger.warning(f"Blocked SSRF probe attempt to {url}")
                continue
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, verify=False) as client:
                    async with client.stream("GET", url) as response:
                        content_chunks = []
                        content_length = 0
                        async for chunk in response.aiter_bytes():
                            content_chunks.append(chunk)
                            content_length += len(chunk)
                            if content_length > 102400: # 100 KB
                                logger.warning(f"Response size exceeded 100KB for {url}, truncating.")
                                break
                        
                        text = b"".join(content_chunks).decode('utf-8', errors='ignore')
                        
                        title = None
                        if 'text/html' in response.headers.get('content-type', ''):
                            soup = BeautifulSoup(text, 'html.parser')
                            if soup.title:
                                title = soup.title.string.strip()[:500] if soup.title.string else None

                        results.append({
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "title": title,
                            "content_length": content_length,
                            "server_header": response.headers.get('server'),
                            "headers": dict(response.headers)
                        })
            except (httpx.TimeoutException, httpx.RequestError) as e:
                logger.debug(f"HTTP Probe error for {url}: {str(e)}")
                pass
        return results

class TechnologyFingerprintService:
    """Technology Fingerprinting"""
    
    @staticmethod
    def extract_fingerprints(probe_data: dict) -> List[dict]:
        fingerprints = []
        headers = probe_data.get('headers', {})
        
        # Check Server header
        server = probe_data.get('server_header', '')
        if server:
            if 'nginx' in server.lower():
                fingerprints.append({"name": "Nginx", "category": "Web Server", "version": server.split('/')[1] if '/' in server else None})
            elif 'apache' in server.lower():
                fingerprints.append({"name": "Apache", "category": "Web Server", "version": server.split('/')[1] if '/' in server else None})
            elif 'cloudflare' in server.lower():
                fingerprints.append({"name": "Cloudflare", "category": "CDN", "version": None})

        # Check X-Powered-By
        powered_by = headers.get('x-powered-by', '')
        if powered_by:
            if 'php' in powered_by.lower():
                fingerprints.append({"name": "PHP", "category": "Programming Language", "version": powered_by.split('/')[1] if '/' in powered_by else None})
            elif 'express' in powered_by.lower():
                fingerprints.append({"name": "Express", "category": "Web Framework", "version": None})
        
        return fingerprints
