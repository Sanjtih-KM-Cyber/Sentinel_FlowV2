"""add evidence validation

Revision ID: 004_add_evidence_validation
Revises: 003_add_obs_find
Create Date: 2026-06-01 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_evidence_validation'
down_revision = '003_add_obs_find'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('evidence', sa.Column('validation_status', sa.String(length=50), nullable=True))

def downgrade() -> None:
    op.drop_column('evidence', 'validation_status')
