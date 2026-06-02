import asyncio
import uuid
import sys

from app.db.session import SessionLocal
from app.api.deps import get_db
from app.repositories.organization import organization as crud_org
from app.schemas.organization import OrganizationUpdate, WorkspaceType
from fastapi.encoders import jsonable_encoder
from app.models.organization import Organization

def run_trace():
    db = SessionLocal()
    org = db.query(Organization).first()
    if not org:
        print("No organization found")
        sys.exit(1)
        
    print(f"Initial DB: {org.workspace_type}")
    
    org_obj = crud_org.get_active(db, org.id)
    print("\nTracing jsonable_encoder:")
    obj_data = jsonable_encoder(org_obj)
    print("Keys in obj_data:", list(obj_data.keys()))
    print("Does obj_data contain 'workspace_type'? ", 'workspace_type' in obj_data)
    
    if 'workspace_type' not in obj_data:
        print("\nEXPECTED BEHAVIOR: jsonable_encoder should include 'workspace_type'")
        print("ACTUAL BEHAVIOR: 'workspace_type' is missing because it's a new schema field or SQLAlchemy attribute cache issue.")
        print("BUG FOUND: db_obj JSON encoder omits 'workspace_type', causing base.py update loop to ignore it.")

run_trace()
