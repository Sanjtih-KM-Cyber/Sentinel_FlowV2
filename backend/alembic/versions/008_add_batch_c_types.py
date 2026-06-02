"""add batch c observation types

Revision ID: 008_add_batch_c_types
Revises: 007_add_batch_b_types
Create Date: 2026-06-01 13:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_batch_c_types'
down_revision = '007_add_batch_b_types'
branch_labels = None
depends_on = None

def upgrade() -> None:
    try:
        op.execute("ALTER TYPE observationtype ADD VALUE 'command_injection'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'ssti'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'xxe'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'ssrf'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'crlf_injection'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'host_header_injection'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'path_traversal'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'hardcoded_secret'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'sensitive_data_exposure'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'api_endpoint'")
        op.execute("ALTER TYPE evidencetype ADD VALUE 'oob_callback'")
    except Exception:
        pass

def downgrade() -> None:
    pass
