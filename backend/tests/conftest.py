import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run API smoke tests.")
    if "test" not in test_database_url.lower():
        pytest.fail("TEST_DATABASE_URL must point to a database with 'test' in its name.")

    os.environ["DATABASE_URL"] = test_database_url
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

    from app import models  # noqa: F401
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
