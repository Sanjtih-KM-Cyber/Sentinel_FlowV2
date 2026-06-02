import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ObservationType(str, enum.Enum):
    REFLECTED_INPUT = "reflected_input"
    SQL_ERROR = "sql_error"
    SERVER_ERROR = "server_error"
    EXPOSED_FILE = "exposed_file"
    WEAK_HEADER = "weak_header"
    DNS_MISCONFIGURATION = "dns_misconfiguration"
    INSECURE_COOKIE = "insecure_cookie"
    WEAK_TLS = "weak_tls"
    ADMIN_PANEL = "admin_panel"
    OPEN_REDIRECT = "open_redirect"
    CORS_MISCONFIG = "cors_misconfig"
    JWT_ISSUE = "jwt_issue"
    SQL_INJECTION = "sql_injection"
    CROSS_SITE_SCRIPTING = "cross_site_scripting"
    HTTP_TRACE_ENABLED = "http_trace_enabled"
    WAF_DETECTED = "waf_detected"
    OPEN_PORT = "open_port"
    TECHNOLOGY_FINGERPRINT = "technology_fingerprint"
    CLICKJACKING = "clickjacking"
    COMMAND_INJECTION = "command_injection"
    SSTI = "ssti"
    XXE = "xxe"
    SSRF = "ssrf"
    CRLF_INJECTION = "crlf_injection"
    HOST_HEADER_INJECTION = "host_header_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    API_ENDPOINT = "api_endpoint"
    LDAP_INJECTION = "ldap_injection"
    XPATH_INJECTION = "xpath_injection"
    GRAPHQL_SECURITY = "graphql_security"
    DEFAULT_CREDENTIALS = "default_credentials"
    MASS_ASSIGNMENT = "mass_assignment"
    IDOR = "idor"
    CSRF = "csrf"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    BUSINESS_LOGIC = "business_logic"
    PROTOTYPE_POLLUTION = "prototype_pollution"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    SUBDOMAIN_TAKEOVER = "subdomain_takeover"

class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint('org_id', 'asset_id', 'observation_type', 'fingerprint', name='uq_observation_dedup'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    observation_type = Column(Enum(ObservationType, name="observationtype", create_type=False), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    fingerprint = Column(String(255), nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
