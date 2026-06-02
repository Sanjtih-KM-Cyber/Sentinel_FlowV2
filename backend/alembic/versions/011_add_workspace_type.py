"""add workspace type

Revision ID: 011_add_workspace_type
Revises: 010_application_mapping
Create Date: 2026-06-02 06:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_add_workspace_type'
down_revision = '010_application_mapping'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ENUM type
    workspace_type = postgresql.ENUM('SOLO', 'AGENCY', 'ENTERPRISE', name='workspacetype')
    workspace_type.create(op.get_bind(), checkfirst=True)

    # Add column
    op.add_column('organizations', sa.Column('workspace_type', workspace_type, server_default='SOLO', nullable=False))
    
    # Backfill explicitly just to be safe
    op.execute("UPDATE organizations SET workspace_type = 'SOLO' WHERE workspace_type IS NULL")

def downgrade() -> None:
    # Drop column
    op.drop_column('organizations', 'workspace_type')

    # Drop ENUM type
    workspace_type = postgresql.ENUM('SOLO', 'AGENCY', 'ENTERPRISE', name='workspacetype')
    workspace_type.drop(op.get_bind(), checkfirst=True)
