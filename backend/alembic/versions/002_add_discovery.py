"""add discovery layer

Revision ID: 002_add_discovery
Revises: 001_add_assets
Create Date: 2026-06-01 05:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_discovery'
down_revision = '001_add_assets'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create Enums
    discoverystatus = postgresql.ENUM('pending', 'running', 'completed', 'failed', name='discoverystatus')
    discoverystatus.create(op.get_bind())
    
    assetsource = postgresql.ENUM('crt_sh', 'hackertarget', 'manual', 'passive_dns', name='assetsource')
    assetsource.create(op.get_bind())
    
    dnsrecordtype = postgresql.ENUM('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', name='dnsrecordtype')
    dnsrecordtype.create(op.get_bind())

    # Create discovery_jobs
    op.create_table('discovery_jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', name='discoverystatus', create_type=False), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovery_jobs_id'), 'discovery_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_discovery_jobs_org_id'), 'discovery_jobs', ['org_id'], unique=False)
    op.create_index(op.f('ix_discovery_jobs_project_id'), 'discovery_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_discovery_jobs_asset_id'), 'discovery_jobs', ['asset_id'], unique=False)

    # Create discovered_assets
    op.create_table('discovered_assets',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('discovery_job_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('source', postgresql.ENUM('crt_sh', 'hackertarget', 'manual', 'passive_dns', name='assetsource', create_type=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['discovery_job_id'], ['discovery_jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_asset_id'], ['assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('parent_asset_id', 'name', name='uq_discovered_asset_parent_name')
    )
    op.create_index(op.f('ix_discovered_assets_id'), 'discovered_assets', ['id'], unique=False)
    op.create_index(op.f('ix_discovered_assets_org_id'), 'discovered_assets', ['org_id'], unique=False)
    op.create_index(op.f('ix_discovered_assets_discovery_job_id'), 'discovered_assets', ['discovery_job_id'], unique=False)
    op.create_index(op.f('ix_discovered_assets_parent_asset_id'), 'discovered_assets', ['parent_asset_id'], unique=False)
    op.create_index(op.f('ix_discovered_assets_name'), 'discovered_assets', ['name'], unique=False)
    op.create_index(op.f('ix_discovered_assets_source'), 'discovered_assets', ['source'], unique=False)

    # Create dns_records
    op.create_table('dns_records',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('discovered_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('record_type', postgresql.ENUM('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', name='dnsrecordtype', create_type=False), nullable=False),
    sa.Column('value', sa.String(length=1024), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['discovered_asset_id'], ['discovered_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dns_records_id'), 'dns_records', ['id'], unique=False)
    op.create_index(op.f('ix_dns_records_discovered_asset_id'), 'dns_records', ['discovered_asset_id'], unique=False)

    # Create http_probes
    op.create_table('http_probes',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('discovered_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('url', sa.String(length=2048), nullable=False),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=512), nullable=True),
    sa.Column('content_length', sa.Integer(), nullable=True),
    sa.Column('server_header', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['discovered_asset_id'], ['discovered_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_http_probes_id'), 'http_probes', ['id'], unique=False)
    op.create_index(op.f('ix_http_probes_discovered_asset_id'), 'http_probes', ['discovered_asset_id'], unique=False)

    # Create technology_fingerprints
    op.create_table('technology_fingerprints',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('http_probe_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('category', sa.String(length=255), nullable=True),
    sa.Column('version', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['http_probe_id'], ['http_probes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_technology_fingerprints_id'), 'technology_fingerprints', ['id'], unique=False)
    op.create_index(op.f('ix_technology_fingerprints_http_probe_id'), 'technology_fingerprints', ['http_probe_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_technology_fingerprints_http_probe_id'), table_name='technology_fingerprints')
    op.drop_index(op.f('ix_technology_fingerprints_id'), table_name='technology_fingerprints')
    op.drop_table('technology_fingerprints')
    
    op.drop_index(op.f('ix_http_probes_discovered_asset_id'), table_name='http_probes')
    op.drop_index(op.f('ix_http_probes_id'), table_name='http_probes')
    op.drop_table('http_probes')
    
    op.drop_index(op.f('ix_dns_records_discovered_asset_id'), table_name='dns_records')
    op.drop_index(op.f('ix_dns_records_id'), table_name='dns_records')
    op.drop_table('dns_records')
    
    op.drop_index(op.f('ix_discovered_assets_name'), table_name='discovered_assets')
    op.drop_index(op.f('ix_discovered_assets_source'), table_name='discovered_assets')
    op.drop_index(op.f('ix_discovered_assets_parent_asset_id'), table_name='discovered_assets')
    op.drop_index(op.f('ix_discovered_assets_discovery_job_id'), table_name='discovered_assets')
    op.drop_index(op.f('ix_discovered_assets_org_id'), table_name='discovered_assets')
    op.drop_index(op.f('ix_discovered_assets_id'), table_name='discovered_assets')
    op.drop_table('discovered_assets')
    
    op.drop_index(op.f('ix_discovery_jobs_asset_id'), table_name='discovery_jobs')
    op.drop_index(op.f('ix_discovery_jobs_project_id'), table_name='discovery_jobs')
    op.drop_index(op.f('ix_discovery_jobs_org_id'), table_name='discovery_jobs')
    op.drop_index(op.f('ix_discovery_jobs_id'), table_name='discovery_jobs')
    op.drop_table('discovery_jobs')

    postgresql.ENUM('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', name='dnsrecordtype').drop(op.get_bind())
    postgresql.ENUM('crt_sh', 'hackertarget', 'manual', 'passive_dns', name='assetsource').drop(op.get_bind())
    postgresql.ENUM('pending', 'running', 'completed', 'failed', name='discoverystatus').drop(op.get_bind())
