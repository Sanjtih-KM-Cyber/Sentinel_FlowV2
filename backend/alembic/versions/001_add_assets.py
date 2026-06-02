"""add assets

Revision ID: 001_add_assets
Revises: 
Create Date: 2026-06-01 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_assets'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # We create the enums
    assettype = postgresql.ENUM('domain', 'subdomain', 'url', name='assettype')
    assettype.create(op.get_bind())
    
    assetstatus = postgresql.ENUM('pending_verification', 'verified', 'verification_failed', 'archived', name='assetstatus')
    assetstatus.create(op.get_bind())
    
    verificationmethod = postgresql.ENUM('dns_txt', 'html_file', 'meta_tag', name='verificationmethod')
    verificationmethod.create(op.get_bind())

    op.create_table('assets',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('asset_type', postgresql.ENUM('domain', 'subdomain', 'url', name='assettype', create_type=False), nullable=False),
    sa.Column('status', postgresql.ENUM('pending_verification', 'verified', 'verification_failed', 'archived', name='assetstatus', create_type=False), nullable=False),
    sa.Column('is_archived', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)
    op.create_index(op.f('ix_assets_org_id'), 'assets', ['org_id'], unique=False)
    op.create_index(op.f('ix_assets_project_id'), 'assets', ['project_id'], unique=False)
    op.create_unique_constraint('uq_asset_org_name', 'assets', ['org_id', 'name'])

    op.create_table('asset_verifications',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('method', postgresql.ENUM('dns_txt', 'html_file', 'meta_tag', name='verificationmethod', create_type=False), nullable=False),
    sa.Column('verification_token', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_verifications_id'), 'asset_verifications', ['id'], unique=False)
    op.create_index(op.f('ix_asset_verifications_asset_id'), 'asset_verifications', ['asset_id'], unique=False)
    op.create_index(op.f('ix_asset_verifications_verification_token'), 'asset_verifications', ['verification_token'], unique=True)


def downgrade() -> None:
    op.drop_constraint('uq_asset_org_name', 'assets', type_='unique')
    op.drop_index(op.f('ix_asset_verifications_verification_token'), table_name='asset_verifications')
    op.drop_index(op.f('ix_asset_verifications_asset_id'), table_name='asset_verifications')
    op.drop_index(op.f('ix_asset_verifications_id'), table_name='asset_verifications')
    op.drop_table('asset_verifications')
    
    op.drop_index(op.f('ix_assets_project_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_org_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_id'), table_name='assets')
    op.drop_table('assets')

    postgresql.ENUM('dns_txt', 'html_file', 'meta_tag', name='verificationmethod').drop(op.get_bind())
    postgresql.ENUM('pending_verification', 'verified', 'verification_failed', 'archived', name='assetstatus').drop(op.get_bind())
    postgresql.ENUM('domain', 'subdomain', 'url', name='assettype').drop(op.get_bind())
