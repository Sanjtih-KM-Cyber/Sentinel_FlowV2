import pytest
import uuid
import httpx
from typing import Generator
from app.models.application_mapping import ApplicationSession, DiscoveredEndpoint, DiscoveredParameter, DiscoveredObject, Workflow, WorkflowStep
from app.services.mapping_services import (
    AuthenticatedCrawlerService,
    FormDiscoveryService,
    ParameterDiscoveryService,
    JavaScriptAnalysisService,
    ObjectDiscoveryService,
    WorkflowDiscoveryService,
    AuthorizationContextService,
    StateTrackingService
)
from app.schemas.application_mapping import DiscoveredObjectCreate

def test_authorization_context(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    session = AuthorizationContextService.create_context(
        db_session, org_id, project_id, "UserA", {"session": "token-a"}
    )
    
    assert session.session_type == "UserA"
    assert session.cookies == {"session": "token-a"}
    
def test_form_discovery(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    html = '''
    <form action="/login" method="POST">
        <input type="text" name="username" />
        <input type="hidden" name="csrf" value="123" />
    </form>
    '''
    
    endpoints = FormDiscoveryService.discover_forms(db_session, html, "http://test", org_id, project_id)
    assert len(endpoints) == 1
    assert endpoints[0].url == "http://test/login"
    assert endpoints[0].method == "POST"
    
    params = db_session.query(DiscoveredParameter).filter_by(endpoint_id=endpoints[0].id).all()
    assert len(params) == 2
    assert any(p.name == "csrf" and p.is_hidden for p in params)
    
def test_javascript_analysis(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    js = "const data = await fetch('/api/users');"
    endpoints = JavaScriptAnalysisService.analyze_js(db_session, js, "http://test/app.js", org_id, project_id)
    assert len(endpoints) == 1
    assert endpoints[0].url == "http://test/api/users"

def test_object_discovery(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    content = '{"user_id": 42}'
    ep = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="GET", url="http://test/api", source="Crawl")
    db_session.add(ep)
    db_session.commit()
    
    objects = ObjectDiscoveryService.discover_objects(db_session, content, ep.id, org_id, project_id, "UserA")
    assert len(objects) == 1
    assert objects[0].identifier == "42"
    assert objects[0].owner_context == "UserA"
    
def test_param_discovery(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    endpoint = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="GET", url="/test", source="FFUF")
    db_session.add(endpoint)
    db_session.commit()
    
    saved = ParameterDiscoveryService.discover_parameters(
        db_session, endpoint.id, 
        url="http://test?id=1", method="GET"
    )
    assert len(saved) == 1
    assert saved[0].name == "id"
    assert saved[0].default_value == "1"

def test_workflow_discovery(db_session, setup_data):
    org_id = setup_data["org1"].id
    project_id = setup_data["project1"].id
    
    endpoint = DiscoveredEndpoint(org_id=org_id, project_id=project_id, method="POST", url="/login", source="Crawl")
    db_session.add(endpoint)
    db_session.commit()
    
    workflows = WorkflowDiscoveryService.discover_workflows(db_session, [endpoint], org_id, project_id)
    assert len(workflows) == 1
    assert workflows[0].name == "Authentication Flow"
    assert len(workflows[0].steps) == 1

def test_state_tracking_diff():
    before = {"name": "test", "is_admin": False}
    after = {"name": "test", "is_admin": True, "new_field": "123"}
    
    diff = StateTrackingService.generate_diff(before, after)
    assert diff["added"] == {"new_field": "123"}
    assert diff["changed"] == {"is_admin": {"from": False, "to": True}}
    assert diff["removed"] == {}
