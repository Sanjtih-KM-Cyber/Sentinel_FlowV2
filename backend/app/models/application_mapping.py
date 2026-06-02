import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ApplicationSession(Base):
    __tablename__ = "application_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    session_type = Column(String, nullable=False) # e.g., 'Anonymous', 'UserA', 'UserB', 'Admin'
    cookies = Column(JSONB, nullable=True)
    headers = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DiscoveredEndpoint(Base):
    __tablename__ = "discovered_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    method = Column(String, nullable=False)
    url = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False) # Crawl, FFUF, JS, GraphQL
    is_api = Column(Boolean, default=False)
    is_form = Column(Boolean, default=False)
    parameters = relationship("DiscoveredParameter", back_populates="endpoint", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DiscoveredParameter(Base):
    __tablename__ = "discovered_parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("discovered_endpoints.id"), nullable=False)
    name = Column(String, nullable=False)
    param_type = Column(String, nullable=False) # GET, POST, JSON, MULTIPART, HEADER, PATH
    data_type = Column(String, nullable=True) # string, integer, etc.
    is_required = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    default_value = Column(String, nullable=True)
    
    endpoint = relationship("DiscoveredEndpoint", back_populates="parameters")
    
class DiscoveredObject(Base):
    __tablename__ = "discovered_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    object_type = Column(String, nullable=False) # numeric, uuid, slug, etc.
    identifier = Column(String, nullable=False)
    source_endpoint_id = Column(UUID(as_uuid=True), ForeignKey("discovered_endpoints.id"), nullable=True)
    owner_context = Column(String, nullable=True)
    access_context = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False) # e.g., 'login', 'checkout'
    description = Column(String, nullable=True)
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("discovered_endpoints.id"), nullable=True)
    action_type = Column(String, nullable=False) # GET, POST, CLICK, etc.
    payload = Column(JSONB, nullable=True)
    expected_state_change = Column(String, nullable=True)
    
    workflow = relationship("Workflow", back_populates="steps")
