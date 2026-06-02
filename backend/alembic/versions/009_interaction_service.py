"""add interaction service tables

Revision ID: 009_interaction_service
Revises: 008_add_batch_c_types
Create Date: 2026-06-01 13:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_interaction_service'
down_revision = '008_add_batch_c_types'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'interaction_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('source_module', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_interaction_tokens_id'), 'interaction_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_interaction_tokens_token'), 'interaction_tokens', ['token'], unique=True)
    
    op.create_table(
        'interaction_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction_tokens.id'), nullable=False),
        sa.Column('protocol', sa.String(), nullable=False),
        sa.Column('source_ip', sa.String(), nullable=False),
        sa.Column('request_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_interaction_events_id'), 'interaction_events', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_interaction_events_id'), table_name='interaction_events')
    op.drop_table('interaction_events')
    
    op.drop_index(op.f('ix_interaction_tokens_token'), table_name='interaction_tokens')
    op.drop_index(op.f('ix_interaction_tokens_id'), table_name='interaction_tokens')
    op.drop_table('interaction_tokens')
