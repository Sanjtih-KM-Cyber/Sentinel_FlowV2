import uuid
import secrets
import httpx
import socket
import ipaddress
from urllib.parse import urlparse
import dns.asyncresolver
import dns.exception
import dns.resolver
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetStatus
from app.models.asset_verification import AssetVerification, VerificationMethod
from datetime import datetime

class VerificationService:
    @staticmethod
    def generate_verification_token() -> str:
        return f"aegis-{secrets.token_urlsafe(32)}"

    @staticmethod
    def validate_target_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or url
            if not hostname:
                return False
            
            # remove port if present
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    async def verify_dns_txt(domain: str, token: str) -> tuple[bool, str]:
        try:
            target = f"_aegis-verification.{domain}"
            answers = await dns.asyncresolver.resolve(target, 'TXT')
            for rdata in answers:
                for string in rdata.strings:
                    if string.decode('utf-8') == token:
                        return True, None
            return False, "Verification token not found in DNS records"
        except dns.exception.Timeout:
            return False, "DNS resolution timed out"
        except dns.resolver.NXDOMAIN:
            return False, "DNS domain does not exist"
        except dns.resolver.NoAnswer:
            return False, "No TXT records found"
        except dns.exception.DNSException as e:
            return False, f"DNS error: {str(e)}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def verify_html_file(url: str, token: str) -> tuple[bool, str]:
        try:
            base_url = url if "://" in url else f"http://{url}"
            base_url = base_url.rstrip("/")
            target_url = f"{base_url}/aegis-verification.txt"
            
            if not VerificationService.validate_target_url(target_url):
                return False, "Target URL resolves to a prohibited IP address"

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.get(target_url)
                if response.status_code == 200 and token in response.text:
                    return True, None
            return False, f"HTTP {response.status_code} or token missing"
        except httpx.TimeoutException:
            return False, "HTTP request timed out"
        except httpx.RequestError as e:
            return False, f"HTTP request error: {str(e)}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def verify_meta_tag(url: str, token: str) -> tuple[bool, str]:
        try:
            base_url = url if "://" in url else f"http://{url}"
            
            if not VerificationService.validate_target_url(base_url):
                return False, "Target URL resolves to a prohibited IP address"

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.get(base_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    meta_tag = soup.find('meta', attrs={'name': 'aegis-verification'})
                    if meta_tag and meta_tag.get('content') == token:
                        return True, None
            return False, f"HTTP {response.status_code} or meta tag missing"
        except httpx.TimeoutException:
            return False, "HTTP request timed out"
        except httpx.RequestError as e:
            return False, f"HTTP request error: {str(e)}"
        except Exception as e:
            return False, str(e)

    @classmethod
    async def run_verification(cls, db: Session, asset: Asset, verification: AssetVerification) -> tuple[bool, str]:
        try:
            target = asset.name
            if verification.method == VerificationMethod.DNS_TXT:
                return await cls.verify_dns_txt(target, verification.verification_token)
            elif verification.method == VerificationMethod.HTML_FILE:
                return await cls.verify_html_file(target, verification.verification_token)
            elif verification.method == VerificationMethod.META_TAG:
                return await cls.verify_meta_tag(target, verification.verification_token)
            else:
                return False, "Unknown verification method"
        except Exception as e:
            return False, str(e)
