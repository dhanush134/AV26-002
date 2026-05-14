import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.health_data import HealthHeartRateSample, HealthImport
from tests.test_samsung_health_import import _basic_zip


def _create_user(client: TestClient, name: str = "Samsung Import User") -> str:
    response = client.post(
        "/api/v1/users",
        json={
            "full_name": name,
            "age": 36,
            "gender": "female",
            "height_cm": 168,
            "weight_kg": 64,
            "target_age": 90,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _upload(client: TestClient, user_id: str, *, force_reprocess: bool = False) -> dict:
    response = client.post(
        f"/api/health-imports/samsung/upload?user_id={user_id}&force_reprocess={str(force_reprocess).lower()}",
        files={"file": ("DownloadPersonalData_202605142248.zip", _basic_zip(), "application/zip")},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Set TEST_DATABASE_URL to run DB integration tests.")
def test_upload_creates_import_records_daily_summary_and_ai_profile(client: TestClient) -> None:
    user_id = _create_user(client)
    payload = _upload(client, user_id)
    assert payload["storage"]["status"] == "stored"
    assert payload["storage"]["saved_counts"]["heart_rate_samples"] == 2
    assert payload["storage"]["daily_summaries_updated"] >= 1
    assert payload["storage"]["ai_twin_profile_updated"] is True
    assert payload["sleep"]["detected"] is False

    with SessionLocal() as db:
        health_import = db.query(HealthImport).filter_by(user_id=user_id).one()
        assert health_import.user_id.hex == user_id.replace("-", "")
        assert db.query(HealthHeartRateSample).filter_by(user_id=user_id).count() == 2


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Set TEST_DATABASE_URL to run DB integration tests.")
def test_same_zip_is_idempotent_and_force_reprocess_works(client: TestClient) -> None:
    user_id = _create_user(client, "Idempotent User")
    first = _upload(client, user_id)
    second = _upload(client, user_id)
    assert second["storage"]["status"] == "already_imported"
    assert second["storage"]["existing_import_id"] == first["storage"]["import_id"]

    forced = _upload(client, user_id, force_reprocess=True)
    assert forced["storage"]["already_imported"] is False
    with SessionLocal() as db:
        assert db.query(HealthHeartRateSample).filter_by(user_id=user_id).count() == 2


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Set TEST_DATABASE_URL to run DB integration tests.")
def test_health_query_endpoints_are_user_scoped_and_recompute_works(client: TestClient) -> None:
    user_a = _create_user(client, "Scoped A")
    user_b = _create_user(client, "Scoped B")
    _upload(client, user_a)

    overview_a = client.get(f"/api/health/users/{user_a}/overview")
    overview_b = client.get(f"/api/health/users/{user_b}/overview")
    assert overview_a.status_code == 200
    assert overview_b.status_code == 200
    assert overview_a.json()["total_records_by_type"]["heart_rate_samples"] == 2
    assert overview_b.json()["total_records_by_type"]["heart_rate_samples"] == 0

    daily = client.get(f"/api/health/users/{user_a}/daily-summaries")
    heart_rate = client.get(f"/api/health/users/{user_a}/heart-rate")
    steps = client.get(f"/api/health/users/{user_a}/steps")
    stress = client.get(f"/api/health/users/{user_a}/stress")
    context = client.get(f"/api/health/users/{user_a}/ai-twin-context")
    recompute = client.post(f"/api/health/users/{user_a}/recompute-daily-summaries")
    assert daily.status_code == heart_rate.status_code == steps.status_code == stress.status_code == context.status_code == 200
    assert recompute.status_code == 200
    assert recompute.json()["daily_summaries_updated"] >= 1


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Set TEST_DATABASE_URL to run DB integration tests.")
def test_internal_daily_sync_secret(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = _create_user(client, "Sync User")
    _upload(client, user_id)
    missing = client.post("/api/health/internal/daily-sync")
    assert missing.status_code == 401

    monkeypatch.setenv("INTERNAL_SYNC_SECRET", "test-secret")
    get_settings.cache_clear()
    ok = client.post("/api/health/internal/daily-sync", headers={"X-Internal-Sync-Secret": "test-secret"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["users_processed"] >= 1
