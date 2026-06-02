"""add observations and findings

Revision ID: 003_add_obs_find
Revises: 002_add_discovery
Create Date: 2026-06-01 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_obs_find'
down_revision = '002_add_discovery'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Observation
    observationtype = postgresql.ENUM('reflected_input', 'sql_error', 'server_error', 'exposed_file', 'weak_header', 'dns_misconfiguration', name='observationtype')
    observationtype.create(op.get_bind())
    
    op.create_table('observations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('observation_type', postgresql.ENUM('reflected_input', 'sql_error', 'server_error', 'exposed_file', 'weak_header', 'dns_misconfiguration', name='observationtype', create_type=False), nullable=False),
    sa.Column('title', sa.String(length=512), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('fingerprint', sa.String(length=255), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'asset_id', 'observation_type', 'fingerprint', name='uq_observation_dedup')
    )
    op.create_index(op.f('ix_observations_id'), 'observations', ['id'], unique=False)
    op.create_index(op.f('ix_observations_org_id'), 'observations', ['org_id'], unique=False)
    op.create_index(op.f('ix_observations_project_id'), 'observations', ['project_id'], unique=False)
    op.create_index(op.f('ix_observations_asset_id'), 'observations', ['asset_id'], unique=False)
    op.create_index(op.f('ix_observations_observation_type'), 'observations', ['observation_type'], unique=False)
    op.create_index(op.f('ix_observations_fingerprint'), 'observations', ['fingerprint'], unique=False)

    # 2. Evidence
    evidencetype = postgresql.ENUM('request', 'response', 'screenshot', 'html_snapshot', 'dns_record', 'raw_artifact', name='evidencetype')
    evidencetype.create(op.get_bind())
    
    op.create_table('evidence',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_type', postgresql.ENUM('request', 'response', 'screenshot', 'html_snapshot', 'dns_record', 'raw_artifact', name='evidencetype', create_type=False), nullable=False),
    sa.Column('content_hash', sa.String(length=255), nullable=False),
    sa.Column('storage_path', sa.String(length=1024), nullable=True),
    sa.Column('snippet', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'content_hash', name='uq_evidence_org_hash')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_org_id'), 'evidence', ['org_id'], unique=False)
    op.create_index(op.f('ix_evidence_evidence_type'), 'evidence', ['evidence_type'], unique=False)
    op.create_index(op.f('ix_evidence_content_hash'), 'evidence', ['content_hash'], unique=False)

    # 3. VerificationRun
    verificationstatus = postgresql.ENUM('pending', 'running', 'completed', 'failed', name='verificationstatus')
    verificationstatus.create(op.get_bind())
    
    op.create_table('verification_runs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('observation_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('rule_id', sa.String(length=255), nullable=False),
    sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', name='verificationstatus', create_type=False), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_runs_id'), 'verification_runs', ['id'], unique=False)
    op.create_index(op.f('ix_verification_runs_org_id'), 'verification_runs', ['org_id'], unique=False)
    op.create_index(op.f('ix_verification_runs_observation_id'), 'verification_runs', ['observation_id'], unique=False)

    # 4. Findings
    findingstatus = postgresql.ENUM('potential', 'verified', 'assigned', 'in_progress', 'fixed', 'retest_pending', 'closed', 'suppressed', name='findingstatus')
    findingstatus.create(op.get_bind())
    
    severity = postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='severity')
    severity.create(op.get_bind())
    
    op.create_table('findings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('observation_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(length=512), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('remediation', sa.Text(), nullable=True),
    sa.Column('status', postgresql.ENUM('potential', 'verified', 'assigned', 'in_progress', 'fixed', 'retest_pending', 'closed', 'suppressed', name='findingstatus', create_type=False), nullable=False),
    sa.Column('severity', postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='severity', create_type=False), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_findings_id'), 'findings', ['id'], unique=False)
    op.create_index(op.f('ix_findings_org_id'), 'findings', ['org_id'], unique=False)
    op.create_index(op.f('ix_findings_project_id'), 'findings', ['project_id'], unique=False)
    op.create_index(op.f('ix_findings_asset_id'), 'findings', ['asset_id'], unique=False)
    op.create_index(op.f('ix_findings_observation_id'), 'findings', ['observation_id'], unique=False)
    op.create_index(op.f('ix_findings_status'), 'findings', ['status'], unique=False)
    op.create_index(op.f('ix_findings_severity'), 'findings', ['severity'], unique=False)

    # 5. ConfidenceScore
    confidencelevel = postgresql.ENUM('certain', 'high', 'medium', 'low', 'tentative', name='confidencelevel')
    confidencelevel.create(op.get_bind())
    
    op.create_table('confidence_scores',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('finding_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('level', postgresql.ENUM('certain', 'high', 'medium', 'low', 'tentative', name='confidencelevel', create_type=False), nullable=False),
    sa.Column('score_numerical', sa.Float(), nullable=False),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_confidence_scores_id'), 'confidence_scores', ['id'], unique=False)
    op.create_index(op.f('ix_confidence_scores_org_id'), 'confidence_scores', ['org_id'], unique=False)
    op.create_index(op.f('ix_confidence_scores_finding_id'), 'confidence_scores', ['finding_id'], unique=False)

    # 6. FindingEvidence
    op.create_table('finding_evidence',
    sa.Column('finding_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('finding_id', 'evidence_id'),
    sa.UniqueConstraint('finding_id', 'evidence_id', name='uq_finding_evidence')
    )


def downgrade() -> None:
    op.drop_table('finding_evidence')
    
    op.drop_index(op.f('ix_confidence_scores_finding_id'), table_name='confidence_scores')
    op.drop_index(op.f('ix_confidence_scores_org_id'), table_name='confidence_scores')
    op.drop_index(op.f('ix_confidence_scores_id'), table_name='confidence_scores')
    op.drop_table('confidence_scores')
    postgresql.ENUM('certain', 'high', 'medium', 'low', 'tentative', name='confidencelevel').drop(op.get_bind())

    op.drop_index(op.f('ix_findings_severity'), table_name='findings')
    op.drop_index(op.f('ix_findings_status'), table_name='findings')
    op.drop_index(op.f('ix_findings_observation_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_asset_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_project_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_org_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_id'), table_name='findings')
    op.drop_table('findings')
    postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='severity').drop(op.get_bind())
    postgresql.ENUM('potential', 'verified', 'assigned', 'in_progress', 'fixed', 'retest_pending', 'closed', 'suppressed', name='findingstatus').drop(op.get_bind())

    op.drop_index(op.f('ix_verification_runs_observation_id'), table_name='verification_runs')
    op.drop_index(op.f('ix_verification_runs_org_id'), table_name='verification_runs')
    op.drop_index(op.f('ix_verification_runs_id'), table_name='verification_runs')
    op.drop_table('verification_runs')
    postgresql.ENUM('pending', 'running', 'completed', 'failed', name='verificationstatus').drop(op.get_bind())

    op.drop_index(op.f('ix_evidence_content_hash'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_evidence_type'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_org_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_id'), table_name='evidence')
    op.drop_table('evidence')
    postgresql.ENUM('request', 'response', 'screenshot', 'html_snapshot', 'dns_record', 'raw_artifact', name='evidencetype').drop(op.get_bind())

    op.drop_index(op.f('ix_observations_fingerprint'), table_name='observations')
    op.drop_index(op.f('ix_observations_observation_type'), table_name='observations')
    op.drop_index(op.f('ix_observations_asset_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_project_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_org_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_id'), table_name='observations')
    op.drop_table('observations')
    postgresql.ENUM('reflected_input', 'sql_error', 'server_error', 'exposed_file', 'weak_header', 'dns_misconfiguration', name='observationtype').drop(op.get_bind())
