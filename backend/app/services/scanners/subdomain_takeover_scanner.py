import uuid
import json
import httpx
import dns.resolver
from typing import List, Tuple, Any
from sqlalchemy.orm import Session
from app.models.observation import ObservationType, Observation
from app.schemas.observation_finding import ObservationCreate
from app.services.observation_service import ObservationService
from app.services.evidence_service import EvidenceService, EvidenceType
from app.models.user import User

class SubdomainTakeoverScanner:
    @staticmethod
    async def _run_subfinder(target_domain: str) -> List[str]:
        # Using crt.sh for real subdomain discovery as a Subfinder alternative
        subdomains = set()
        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                res = await client.get(f"https://crt.sh/?q=%.{target_domain}&output=json")
                if res.status_code == 200:
                    data = res.json()
                    for item in data:
                        name = item.get("name_value", "")
                        for cur_name in name.split('\n'):
                            if cur_name.endswith(target_domain) and not cur_name.startswith("*"):
                                subdomains.add(cur_name)
        except Exception:
            pass
        return list(subdomains)
        
    @staticmethod
    def _resolve_cname(subdomain: str) -> str:
        try:
            answers = dns.resolver.resolve(subdomain, 'CNAME')
            for rdata in answers:
                return rdata.target.to_text().strip('.')
        except Exception:
            pass
        return None

    @staticmethod
    async def scan(
        target_url: str,
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user: User
    ) -> List[Tuple[Observation, List[Any]]]:
        observations = []
        
        from urllib.parse import urlparse
        domain = urlparse(target_url).netloc
        if ":" in domain:
            domain = domain.split(":")[0]
            
        subdomains = await SubdomainTakeoverScanner._run_subfinder(domain)
        
        # known provider takeover fingerprints (Nuclei template equivalents)
        provider_fingerprints = {
            "s3.amazonaws.com": {
                "name": "AWS S3",
                "vulnerable_body": b"NoSuchBucket",
                "cname": True
            },
            "myshopify.com": {
                "name": "Shopify",
                "vulnerable_body": b"Sorry, this shop is currently unavailable.",
                "cname": True
            }
        }
        
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            for sub in subdomains:
                cname = SubdomainTakeoverScanner._resolve_cname(sub)
                if not cname:
                    continue
                    
                provider = None
                for p_key, p_data in provider_fingerprints.items():
                    if p_key in cname:
                        provider = p_data
                        break
                        
                if not provider:
                    continue
                    
                # DNS record existence alone is insufficient. Validate provider fingerprints.
                try:
                    res = await client.get(f"http://{sub}")
                    
                    # Provider-specific takeover confirmation
                    if provider["vulnerable_body"] in res.content:
                         req_snippet = f"GET http://{sub}\nHost: {sub}"
                         res_snippet = f"HTTP/1.1 {res.status_code} {res.reason_phrase}\n{res.text[:200]}"
                         dns_snippet = f"{sub} CNAME {cname}"
                         
                         ev_req = EvidenceService.store_evidence(db, org_id, EvidenceType.REQUEST, req_snippet)
                         ev_res = EvidenceService.store_evidence(db, org_id, EvidenceType.RESPONSE, res_snippet)
                         ev_dns = EvidenceService.store_evidence(db, org_id, EvidenceType.NETWORK_TRAFFIC, dns_snippet)

                         obs_in = ObservationCreate(
                             org_id=org_id,
                             project_id=project_id,
                             observation_type=ObservationType.SUBDOMAIN_TAKEOVER,
                             title=f"Subdomain Takeover on {sub}",
                             fingerprint=f"subdomain_takeover_{sub}",
                             metadata_json={
                                 "subdomain": sub,
                                 "cname": cname,
                                 "provider": provider["name"],
                                 "verified": True
                             }
                         )
                         obs = ObservationService.create_or_get_observation(db, obs_in, user)
                         observations.append((obs, [ev_req, ev_res, ev_dns]))
                         
                except httpx.RequestError:
                    pass
                    
        return observations
