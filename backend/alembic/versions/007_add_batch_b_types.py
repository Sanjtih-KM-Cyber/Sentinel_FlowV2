"""add batch b observation and evidence types

Revision ID: 007_add_batch_b_types
Revises: 006_add_evidence_network_log
Create Date: 2026-06-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_batch_b_types'
down_revision = '006_add_evidence_network_log'
branch_labels = None
depends_on = None

def upgrade() -> None:
    try:
        op.execute("ALTER TYPE observationtype ADD VALUE 'sql_injection'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'cross_site_scripting'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'http_trace_enabled'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'waf_detected'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'open_port'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'technology_fingerprint'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'clickjacking'")
        
        op.execute("ALTER TYPE evidencetype ADD VALUE 'tool_output'")
    except Exception:
        pass

def downgrade() -> None:
    pass
