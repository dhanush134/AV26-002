import os
import subprocess

import pytest


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") or not os.getenv("RUN_ALEMBIC_MIGRATION_TEST"),
    reason="Set TEST_DATABASE_URL and RUN_ALEMBIC_MIGRATION_TEST=1 to run destructive Alembic migration test.",
)
def test_health_alembic_migration_applies_cleanly() -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = env["TEST_DATABASE_URL"]
    downgrade = subprocess.run(["alembic", "downgrade", "base"], env=env, capture_output=True, text=True, check=False)
    assert downgrade.returncode == 0, downgrade.stderr
    upgrade = subprocess.run(["alembic", "upgrade", "head"], env=env, capture_output=True, text=True, check=False)
    assert upgrade.returncode == 0, upgrade.stderr
