"""add evidence type network_log

Revision ID: 006_add_evidence_network_log
Revises: 005_add_observation_types
Create Date: 2026-06-01 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_evidence_network_log'
down_revision = '005_add_observation_types'
branch_labels = None
depends_on = None

def upgrade() -> None:
    try:
        op.execute("ALTER TYPE evidencetype ADD VALUE 'network_log'")
    except Exception:
        pass # In case it already exists or sqlite workaround needed

def downgrade() -> None:
    pass
