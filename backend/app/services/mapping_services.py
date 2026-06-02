import uuid
import httpx
import re
import json
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from app.models.application_mapping import ApplicationSession, DiscoveredEndpoint, DiscoveredParameter, DiscoveredObject, Workflow, WorkflowStep
from app.schemas.application_mapping import (
    ApplicationSessionCreate, 
    DiscoveredEndpointCreate, 
    DiscoveredParameterCreate,
    DiscoveredObjectCreate
)

class AuthenticatedCrawlerService:
    @staticmethod
    async def crawl(
        db: Session, 
        start_url: str, 
        org_id: uuid.UUID, 
        project_id: uuid.UUID, 
        session_info: ApplicationSession,
        max_depth: int = 3,
        max_pages: int = 50
    ) -> List[DiscoveredEndpoint]:
        
        visited: Set[str] = set()
        queue = deque([(start_url, 0)])
        discovered_endpoints: List[DiscoveredEndpoint] = []
        base_domain = urlparse(start_url).netloc
        
        def is_valid_url(url: str) -> bool:
            parsed = urlparse(url)
            # Domain restriction
            if parsed.netloc and parsed.netloc != base_domain:
                return False
            # Check ignored extensions (basic robots.txt awareness placeholder logic)
            if any(url.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"]):
                return False
            return True

        def normalize_url(base: str, target: str) -> str:
            raw = urljoin(base, target)
            parsed = urlparse(raw)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        async with httpx.AsyncClient(verify=False, cookies=session_info.cookies, headers=session_info.headers, timeout=10.0, follow_redirects=True) as client:
            while queue and len(visited) < max_pages:
                current_url, depth = queue.popleft()
                norm_current = normalize_url(start_url, current_url)
                
                if norm_current in visited or depth > max_depth or not is_valid_url(norm_current):
                    continue
                    
                visited.add(norm_current)

                try:
                    response = await client.get(norm_current)
                    
                    if response.cookies:
                        session_info.cookies = {**(session_info.cookies or {}), **dict(response.cookies)}
                        db.commit()

                    endpoint = DiscoveredEndpoint(
                        org_id=org_id,
                        project_id=project_id,
                        method="GET",
                        url=norm_current,
                        source="Crawl"
                    )
                    db.add(endpoint)
                    db.flush()
                    discovered_endpoints.append(endpoint)

                    if "text/html" in response.headers.get("Content-Type", ""):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for a_tag in soup.find_all('a', href=True):
                            next_url = normalize_url(norm_current, a_tag['href'])
                            if is_valid_url(next_url) and next_url not in visited:
                                queue.append((next_url, depth + 1))
                                
                except httpx.RequestError:
                    continue
                    
        db.commit()
        return discovered_endpoints

class FormDiscoveryService:
    @staticmethod
    def discover_forms(
        db: Session,
        html_content: str,
        source_url: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> List[DiscoveredEndpoint]:
        
        endpoints = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for form in soup.find_all('form'):
            action = form.get('action', source_url)
            method = form.get('method', 'get').upper()
            
            endpoint = DiscoveredEndpoint(
                org_id=org_id,
                project_id=project_id,
                method=method,
                url=urljoin(source_url, action),
                source="Crawl_Form",
                is_form=True
            )
            db.add(endpoint)
            db.flush()
            endpoints.append(endpoint)
            
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                name = input_tag.get('name')
                if not name:
                    continue
                
                input_type = input_tag.get('type', 'text').lower() if input_tag.name == 'input' else input_tag.name
                
                param = DiscoveredParameter(
                    endpoint_id=endpoint.id,
                    name=name,
                    param_type=method,
                    data_type="string",
                    is_hidden=(input_type == 'hidden'),
                    is_required=input_tag.has_attr('required'),
                    default_value=input_tag.get('value')
                )
                db.add(param)
        db.commit()
        return endpoints

class ParameterDiscoveryService:
    @staticmethod
    def discover_parameters(
        db: Session,
        endpoint_id: uuid.UUID,
        url: str,
        method: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> List[DiscoveredParameter]:
        
        saved_params = []
        
        # 1. GET parameters from URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        for name, values in query_params.items():
            param = DiscoveredParameter(
                endpoint_id=endpoint_id,
                name=name,
                param_type="GET",
                data_type="string",
                default_value=values[0] if values else None
            )
            db.add(param)
            saved_params.append(param)
            
        # 2. JSON variables (Body or GraphQL)
        if body and headers and "application/json" in headers.get("Content-Type", ""):
            try:
                json_data = json.loads(body)
                
                def extract_json_keys(data: Any, prefix: str = "") -> None:
                    if isinstance(data, dict):
                        for k, v in data.items():
                            key_path = f"{prefix}.{k}" if prefix else k
                            param = DiscoveredParameter(
                                endpoint_id=endpoint_id,
                                name=key_path,
                                param_type="JSON",
                                data_type=type(v).__name__,
                                default_value=str(v) if not isinstance(v, (dict, list)) else None
                            )
                            db.add(param)
                            saved_params.append(param)
                            extract_json_keys(v, key_path)
                    elif isinstance(data, list) and data:
                        extract_json_keys(data[0], f"{prefix}[]")

                extract_json_keys(json_data)
            except json.JSONDecodeError:
                pass
                
        # 3. Multipart / form-data URL encoded string in body
        if body and method == "POST" and headers and "application/x-www-form-urlencoded" in headers.get("Content-Type", ""):
            post_params = parse_qs(body)
            for name, values in post_params.items():
                param = DiscoveredParameter(
                    endpoint_id=endpoint_id,
                    name=name,
                    param_type="POST",
                    data_type="string",
                    default_value=values[0] if values else None
                )
                db.add(param)
                saved_params.append(param)
                
        db.commit()
        return saved_params

class JavaScriptAnalysisService:
    @staticmethod
    def analyze_js(
        db: Session,
        js_content: str,
        source_url: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> List[DiscoveredEndpoint]:
        
        endpoints = []
        
        # Regex for fetch / axios / XHR / GraphQL
        # Captures string literals inside fetch('...') or axios.get('...')
        api_pattern = re.compile(r"""(?:fetch|axios\.(?:get|post|put|delete)|XMLHttpRequest\.open\(['"](?:GET|POST|PUT|DELETE)['"],\s*)['"](/api/[^'"]+)['"]""")
        graphql_pattern = re.compile(r"""(?:fetch|axios\.post)\(['"]([^'"]*graphql[^'"]*)['"]""")
        route_pattern = re.compile(r"""['"](/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)['"]""")

        found_apis = api_pattern.findall(js_content)
        for api_url in found_apis:
            endpoint = DiscoveredEndpoint(
                org_id=org_id, project_id=project_id, method="GET", # Default assumption, would need deeper AST for real method
                url=urljoin(source_url, api_url), source="JS_API", is_api=True
            )
            db.add(endpoint)
            endpoints.append(endpoint)
            
        found_gql = graphql_pattern.findall(js_content)
        for gql_url in found_gql:
            endpoint = DiscoveredEndpoint(
                org_id=org_id, project_id=project_id, method="POST",
                url=urljoin(source_url, gql_url), source="JS_GraphQL", is_api=True
            )
            db.add(endpoint)
            endpoints.append(endpoint)
            
        found_routes = set(route_pattern.findall(js_content))
        for route in found_routes:
            if route not in found_apis and route not in found_gql:
                endpoint = DiscoveredEndpoint(
                    org_id=org_id, project_id=project_id, method="GET",
                    url=urljoin(source_url, route), source="JS_Route", is_api=False
                )
                db.add(endpoint)
                endpoints.append(endpoint)

        db.commit()
        return endpoints

class ObjectDiscoveryService:
    @staticmethod
    def discover_objects(
        db: Session,
        content: str,
        source_endpoint_id: uuid.UUID,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        owner_context: Optional[str] = None,
        access_context: Optional[str] = None
    ) -> List[DiscoveredObject]:
        
        objects = []
        
        uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
        numeric_id_pattern = re.compile(r'\"(?:id|account_id|document_id|order_id|user_id)\":\s*(\d+)', re.I)
        
        found_uuids = set(uuid_pattern.findall(content))
        for uid in found_uuids:
            obj = DiscoveredObject(
                org_id=org_id, project_id=project_id,
                object_type="uuid", identifier=uid, source_endpoint_id=source_endpoint_id,
                owner_context=owner_context, access_context=access_context
            )
            db.add(obj)
            objects.append(obj)
            
        found_numerics = set(numeric_id_pattern.findall(content))
        for nid in found_numerics:
            obj = DiscoveredObject(
                org_id=org_id, project_id=project_id,
                object_type="numeric", identifier=nid, source_endpoint_id=source_endpoint_id,
                owner_context=owner_context, access_context=access_context
            )
            db.add(obj)
            objects.append(obj)

        db.commit()
        return objects

class WorkflowDiscoveryService:
    @staticmethod
    def discover_workflows(
        db: Session,
        endpoints: List[DiscoveredEndpoint],
        org_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> List[Workflow]:
        """
        Transition discovery and graph generation.
        """
        workflows = []
        login_steps = []
        checkout_steps = []
        
        for ep in endpoints:
            if "login" in ep.url.lower():
                login_steps.append({"endpoint_id": ep.id, "action_type": ep.method, "payload": {}})
            elif "checkout" in ep.url.lower() or "cart" in ep.url.lower():
                checkout_steps.append({"endpoint_id": ep.id, "action_type": ep.method, "payload": {}})
                
        if login_steps:
            wf = Workflow(org_id=org_id, project_id=project_id, name="Authentication Flow")
            db.add(wf)
            db.flush()
            for i, step_data in enumerate(sorted(login_steps, key=lambda x: x["action_type"])):
                 step = WorkflowStep(
                     workflow_id=wf.id, step_order=i, endpoint_id=step_data["endpoint_id"],
                     action_type=step_data["action_type"]
                 )
                 db.add(step)
            workflows.append(wf)
            
        if checkout_steps:
            wf = Workflow(org_id=org_id, project_id=project_id, name="Checkout Flow")
            db.add(wf)
            db.flush()
            for i, step_data in enumerate(sorted(checkout_steps, key=lambda x: x["action_type"])):
                 step = WorkflowStep(
                     workflow_id=wf.id, step_order=i, endpoint_id=step_data["endpoint_id"],
                     action_type=step_data["action_type"]
                 )
                 db.add(step)
            workflows.append(wf)

        db.commit()
        return workflows

class StateTrackingService:
    @staticmethod
    async def capture_state(
        client: httpx.AsyncClient,
        endpoint_url: str
    ) -> Dict[str, Any]:
        try:
             res = await client.get(endpoint_url)
             if res.status_code == 200:
                  return res.json()
        except:
             pass
        return {}
        
    @staticmethod
    def generate_diff(state_before: Dict[str, Any], state_after: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        for k, v in state_after.items():
            if k not in state_before:
                diff["added"][k] = v
            elif state_before[k] != v:
                diff["changed"][k] = {"from": state_before[k], "to": v}
                
        for k, v in state_before.items():
            if k not in state_after:
                diff["removed"][k] = v
                
        return diff

class AuthorizationContextService:
    @staticmethod
    def get_context(
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        session_type: str
    ) -> Optional[ApplicationSession]:
        return db.query(ApplicationSession).filter(
            ApplicationSession.org_id == org_id,
            ApplicationSession.project_id == project_id,
            ApplicationSession.session_type == session_type
        ).first()

    @staticmethod
    def create_context(
        db: Session,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        session_type: str,
        cookies: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> ApplicationSession:
        
        valid_types = ["Anonymous", "UserA", "UserB", "Admin"]
        if session_type not in valid_types:
            session_type = "Anonymous"
            
        session = ApplicationSession(
            org_id=org_id,
            project_id=project_id,
            session_type=session_type,
            cookies=cookies,
            headers=headers
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

