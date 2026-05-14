from fastapi.testclient import TestClient


def _create_demo(client: TestClient) -> str:
    response = client.post("/api/v1/demo/run-full-demo")
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["user_id"]
    return payload["user_id"]


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_demo_user_or_run_full_demo(client: TestClient) -> None:
    response = client.post("/api/v1/demo/run-full-demo")
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["message"] == "LifeTwin AI demo user created successfully."
    assert "dashboard" in payload["next_steps"]


def test_dashboard_response_shape(client: TestClient) -> None:
    user_id = _create_demo(client)
    response = client.get(f"/api/v1/users/{user_id}/dashboard")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user"]["id"] == user_id
    assert payload["current_status"]["overall_risk_level"] in {"low", "moderate", "high", "critical"}
    assert "heart_rate_trend" in payload["charts"]
    assert isinstance(payload["today_actions"], list)
    assert payload["disclaimer"]


def test_risk_calculation(client: TestClient) -> None:
    user_id = _create_demo(client)
    response = client.post(f"/api/v1/users/{user_id}/risk/calculate")
    assert response.status_code == 201, response.text
    payload = response.json()
    assert 0 <= payload["cardio_score"] <= 100
    assert payload["overall_risk_level"] in {"low", "moderate", "high", "critical"}
    assert payload["disclaimer"]


def test_simulation_replay(client: TestClient) -> None:
    user_id = _create_demo(client)
    response = client.post(
        f"/api/v1/users/{user_id}/simulation/replay",
        json={"scenario": "cardiac_strain", "points": 30},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user"]["id"] == user_id
    assert payload["current_status"]["anomaly_score"] >= 0
    assert len(payload["charts"]["heart_rate_trend"]) > 0


def test_doctor_report(client: TestClient) -> None:
    user_id = _create_demo(client)
    response = client.get(f"/api/v1/users/{user_id}/doctor-report")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user_id"] == user_id
    assert "latest_vitals_summary" in payload
    assert payload["disclaimer"]
