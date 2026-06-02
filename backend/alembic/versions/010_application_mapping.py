"""add application mapping models

Revision ID: 010_application_mapping
Revises: 009_interaction_service
Create Date: 2026-06-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_application_mapping'
down_revision = '009_interaction_service'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # application_sessions
    op.create_table(
        'application_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('session_type', sa.String(), nullable=False),
        sa.Column('cookies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_application_sessions_id'), 'application_sessions', ['id'], unique=False)

    # discovered_endpoints
    op.create_table(
        'discovered_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('is_api', sa.Boolean(), nullable=True),
        sa.Column('is_form', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_discovered_endpoints_id'), 'discovered_endpoints', ['id'], unique=False)
    op.create_index(op.f('ix_discovered_endpoints_url'), 'discovered_endpoints', ['url'], unique=False)

    # discovered_parameters
    op.create_table(
        'discovered_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovered_endpoints.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('param_type', sa.String(), nullable=False),
        sa.Column('data_type', sa.String(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('is_hidden', sa.Boolean(), nullable=True),
        sa.Column('default_value', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_discovered_parameters_id'), 'discovered_parameters', ['id'], unique=False)

    # discovered_objects
    op.create_table(
        'discovered_objects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('object_type', sa.String(), nullable=False),
        sa.Column('identifier', sa.String(), nullable=False),
        sa.Column('source_endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovered_endpoints.id'), nullable=True),
        sa.Column('owner_context', sa.String(), nullable=True),
        sa.Column('access_context', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_discovered_objects_id'), 'discovered_objects', ['id'], unique=False)

    # workflows
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_workflows_id'), 'workflows', ['id'], unique=False)

    # workflow_steps
    op.create_table(
        'workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovered_endpoints.id'), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_state_change', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_workflow_steps_id'), 'workflow_steps', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('workflow_steps')
    op.drop_table('workflows')
    op.drop_table('discovered_objects')
    op.drop_table('discovered_parameters')
    op.drop_table('discovered_endpoints')
    op.drop_table('application_sessions')
