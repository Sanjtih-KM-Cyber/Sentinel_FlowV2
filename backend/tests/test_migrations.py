import pytest
from alembic.config import Config
from alembic import command
import os
from sqlalchemy import create_engine
from app.core.config import settings

@pytest.mark.asyncio
async def test_migrations_up_down():
    """
    Test that migrations can run up and down.
    This also verifies the workspace_type enum creation and drop steps.
    """
    # Create an alembic config
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), '..', 'alembic'))
    
    # We assume the database is already migrated to head by the test setup
    # so we'll test downgrading one step and upgrading back.
    # The revision is '011_add_workspace_type' and it shouldn't crash.
    
    try:
        command.downgrade(alembic_cfg, "-1")
        command.upgrade(alembic_cfg, "head")
        assert True
    except Exception as e:
        pytest.fail(f"Migration up/down failed: {e}")
