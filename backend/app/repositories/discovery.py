from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.models.discovery_job import DiscoveryJob, DiscoveryStatus
from app.models.discovered_asset import DiscoveredAsset
from app.models.dns_record import DnsRecord
from app.models.http_probe import HttpProbe
from app.models.technology_fingerprint import TechnologyFingerprint
from app.schemas.discovery import DiscoveryJobCreate, DiscoveryJobUpdate, DiscoveredAssetCreate, DnsRecordCreate, HttpProbeCreate, TechnologyFingerprintCreate
from app.repositories.base import CRUDBase

class CRUDDiscoveryJob(CRUDBase[DiscoveryJob, DiscoveryJobCreate, DiscoveryJobUpdate]):
    def create_job(self, db: Session, *, obj_in: DiscoveryJobCreate, commit: bool = True) -> DiscoveryJob:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

    def get_by_org_and_asset(self, db: Session, *, org_id: uuid.UUID, asset_id: uuid.UUID) -> List[DiscoveryJob]:
        return db.query(self.model).filter(
            DiscoveryJob.org_id == org_id,
            DiscoveryJob.asset_id == asset_id
        ).order_by(DiscoveryJob.created_at.desc()).all()

    def get_by_org_and_id(self, db: Session, *, org_id: uuid.UUID, id: uuid.UUID) -> Optional[DiscoveryJob]:
        return db.query(self.model).filter(
            DiscoveryJob.org_id == org_id,
            DiscoveryJob.id == id
        ).first()

class CRUDDiscoveredAsset(CRUDBase[DiscoveredAsset, DiscoveredAssetCreate, DiscoveredAssetCreate]):
    def create_asset(self, db: Session, *, obj_in: DiscoveredAssetCreate, commit: bool = True) -> DiscoveredAsset:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj
        
    def get_by_job(self, db: Session, *, job_id: uuid.UUID) -> List[DiscoveredAsset]:
        return db.query(self.model).filter(DiscoveredAsset.discovery_job_id == job_id).all()

class CRUDDnsRecord(CRUDBase[DnsRecord, DnsRecordCreate, DnsRecordCreate]):
    def create_record(self, db: Session, *, obj_in: DnsRecordCreate, commit: bool = True) -> DnsRecord:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

class CRUDHttpProbe(CRUDBase[HttpProbe, HttpProbeCreate, HttpProbeCreate]):
    def create_probe(self, db: Session, *, obj_in: HttpProbeCreate, commit: bool = True) -> HttpProbe:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

class CRUDTechnologyFingerprint(CRUDBase[TechnologyFingerprint, TechnologyFingerprintCreate, TechnologyFingerprintCreate]):
    def create_fingerprint(self, db: Session, *, obj_in: TechnologyFingerprintCreate, commit: bool = True) -> TechnologyFingerprint:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

discovery_job = CRUDDiscoveryJob(DiscoveryJob)
discovered_asset = CRUDDiscoveredAsset(DiscoveredAsset)
dns_record = CRUDDnsRecord(DnsRecord)
http_probe = CRUDHttpProbe(HttpProbe)
technology_fingerprint = CRUDTechnologyFingerprint(TechnologyFingerprint)
