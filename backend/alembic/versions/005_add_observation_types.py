"""add observation types

Revision ID: 005_add_observation_types
Revises: 004_add_evidence_validation
Create Date: 2026-06-01 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_observation_types'
down_revision = '004_add_evidence_validation'
branch_labels = None
depends_on = None

def upgrade() -> None:
    try:
        op.execute("ALTER TYPE observationtype ADD VALUE 'insecure_cookie'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'weak_tls'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'admin_panel'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'open_redirect'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'cors_misconfig'")
        op.execute("ALTER TYPE observationtype ADD VALUE 'jwt_issue'")
    except Exception:
        pass # In case they already exist or sqlite workaround needed

def downgrade() -> None:
    pass
