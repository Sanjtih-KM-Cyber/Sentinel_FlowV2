import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.api.deps import get_db
from app.models.interaction import InteractionToken, InteractionEvent
from app.services.interaction_service import InteractionService
from app.schemas.interaction import InteractionTokenCreate

def test_interaction_service_token_generation(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    token_in = InteractionTokenCreate(
        org_id=org_id,
        project_id=project_id,
        source_module="TEST_MODULE"
    )
    
    token = InteractionService.generate_token(db_session, token_in)
    assert token.token is not None
    assert token.source_module == "TEST_MODULE"
    
    token_db = InteractionService.get_token(db_session, token.token)
    assert token_db is not None
    assert token_db.id == token.id

@pytest.mark.asyncio
async def test_api_oob_receiver(db_session: Session, setup_data: dict):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    token_in = InteractionTokenCreate(
        org_id=org_id,
        project_id=project_id,
        source_module="SSRF"
    )
    token = InteractionService.generate_token(db_session, token_in)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/oob/{token.token}")
        
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    events = InteractionService.get_events_for_token(db_session, token.token)
    assert len(events) == 1
    assert events[0].protocol == "HTTP"
