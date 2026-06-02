import asyncio
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.discovery_job import DiscoveryJob, DiscoveryStatus
from app.models.discovered_asset import AssetSource
from app.schemas.discovery import DiscoveredAssetCreate, DnsRecordCreate, HttpProbeCreate, TechnologyFingerprintCreate, DiscoveryJobUpdate
from app.repositories.discovery import discovered_asset, dns_record, http_probe, technology_fingerprint, discovery_job
from app.services.discovery_providers import SubdomainProviderCRTsh, DnsIntelligenceProvider, HttpProbingProvider, TechnologyFingerprintService

class DiscoveryPipeline:
    @staticmethod
    async def execute_discovery(db: Session, job: DiscoveryJob, asset: Asset):
        # Update status to running
        discovery_job.update(db=db, db_obj=job, obj_in=DiscoveryJobUpdate(
            status=DiscoveryStatus.RUNNING,
            started_at=datetime.utcnow()
        ), commit=True)
        
        try:
            if asset.asset_type == AssetType.DOMAIN and asset.status == AssetStatus.VERIFIED:
                target_domain = asset.name
                
                # 1. Subdomain Enumeration
                subdomains = await SubdomainProviderCRTsh.discover(target_domain)
                # Ensure base domain is also included
                if target_domain not in subdomains:
                    subdomains.append(target_domain)
                
                for subdomain in set(subdomains):
                    from app.models.discovered_asset import DiscoveredAsset
                    from app.models.dns_record import DnsRecord
                    from app.models.http_probe import HttpProbe
                    
                    new_asset = db.query(DiscoveredAsset).filter(
                        DiscoveredAsset.parent_asset_id == asset.id,
                        DiscoveredAsset.name == subdomain
                    ).first()

                    if new_asset:
                        new_asset.discovery_job_id = job.id
                        db.query(DnsRecord).filter(DnsRecord.discovered_asset_id == new_asset.id).delete()
                        db.query(HttpProbe).filter(HttpProbe.discovered_asset_id == new_asset.id).delete()
                        db.commit()
                    else:
                        # Create discovered asset
                        new_asset = discovered_asset.create_asset(db=db, obj_in=DiscoveredAssetCreate(
                            org_id=asset.org_id,
                            discovery_job_id=job.id,
                            parent_asset_id=asset.id,
                            name=subdomain,
                            source=AssetSource.CRT_SH
                        ), commit=False)
                        
                        db.commit()
                        db.refresh(new_asset)
                    
                    # 2. DNS Intelligence
                    dns_results = await DnsIntelligenceProvider.collect(subdomain)
                    for rtype, records in dns_results.items():
                        for record in records:
                            dns_record.create_record(db=db, obj_in=DnsRecordCreate(
                                discovered_asset_id=new_asset.id,
                                record_type=rtype,
                                value=record
                            ), commit=False)
                            
                    # 3. HTTP Probing
                    http_results = await HttpProbingProvider.probe(subdomain)
                    for probe_res in http_results:
                        new_probe = http_probe.create_probe(db=db, obj_in=HttpProbeCreate(
                            discovered_asset_id=new_asset.id,
                            url=probe_res["url"],
                            status_code=probe_res["status_code"],
                            title=probe_res["title"],
                            content_length=probe_res["content_length"],
                            server_header=probe_res["server_header"]
                        ), commit=False)
                        
                        db.commit()
                        db.refresh(new_probe)
                        
                        # 4. Fingerprinting
                        fingerprints = TechnologyFingerprintService.extract_fingerprints(probe_res)
                        for fp in fingerprints:
                            technology_fingerprint.create_fingerprint(db=db, obj_in=TechnologyFingerprintCreate(
                                http_probe_id=new_probe.id,
                                name=fp["name"],
                                category=fp["category"],
                                version=fp["version"]
                            ), commit=False)
                            
                    db.commit()

            # Mark completed
            discovery_job.update(db=db, db_obj=job, obj_in=DiscoveryJobUpdate(
                status=DiscoveryStatus.COMPLETED,
                completed_at=datetime.utcnow()
            ), commit=True)
            
            from app.services.audit_service import log_audit_event
            # user and request are context dependent, since it's background we'll skip request, user is system?
            # Or pass user to pipeline. We will log without request/user for background tasks.
            log_audit_event(
                db=db,
                org_id=asset.org_id,
                user=None,
                action="discovery.completed",
                resource_type="discovery_job",
                resource_id=str(job.id),
                request=None,
                commit=True
            )

        except Exception as e:
            db.rollback()
            discovery_job.update(db=db, db_obj=job, obj_in=DiscoveryJobUpdate(
                status=DiscoveryStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow()
            ), commit=True)
            
            from app.services.audit_service import log_audit_event
            log_audit_event(
                db=db,
                org_id=asset.org_id,
                user=None,
                action="discovery.failed",
                resource_type="discovery_job",
                resource_id=str(job.id),
                request=None,
                commit=True
            )
