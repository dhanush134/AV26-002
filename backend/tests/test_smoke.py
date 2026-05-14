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


def test_upsert_biomarker_values(client: TestClient) -> None:
    user_id = _create_demo(client)

    create_response = client.put(
        f"/api/v1/users/{user_id}/biomarkers",
        json={
            "hba1c": 5.4,
            "bp_systolic": 118,
            "bp_diastolic": 76,
            "vitamin_d": 34,
            "vitamin_b12": 540,
        },
    )
    assert create_response.status_code == 200, create_response.text
    created = create_response.json()
    assert created["hba1c"] == 5.4
    assert created["bp_systolic"] == 118
    assert created["vitamin_d"] == 34

    update_response = client.put(
        f"/api/v1/users/{user_id}/biomarkers",
        json={
            "hba1c": 5.8,
            "bp_systolic": 124,
            "bp_diastolic": 80,
            "vitamin_d": 41,
            "vitamin_b12": 620,
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["hba1c"] == 5.8
    assert updated["bp_systolic"] == 124
    assert updated["vitamin_b12"] == 620

    invalid_response = client.put(
        f"/api/v1/users/{user_id}/biomarkers",
        json={"bp_systolic": 124},
    )
    assert invalid_response.status_code == 422


def test_update_user_bmi_metrics(client: TestClient) -> None:
    user_id = _create_demo(client)
    response = client.patch(
        f"/api/v1/users/{user_id}",
        json={"age": 36, "height_cm": 181.5, "weight_kg": 82.2},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["id"] == user_id
    assert payload["age"] == 36
    assert payload["height_cm"] == 181.5
    assert payload["weight_kg"] == 82.2


def test_delete_user_clears_single_user_flow(client: TestClient) -> None:
    user_id = _create_demo(client)
    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204, delete_response.text

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404
