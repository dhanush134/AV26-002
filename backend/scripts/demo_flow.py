import os

import httpx


BASE_URL = os.getenv("LIFETWIN_API_URL", "http://localhost:8000")


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=20.0) as client:
        demo = client.post("/api/v1/demo/run-full-demo")
        demo.raise_for_status()
        demo_payload = demo.json()
        user_id = demo_payload["user_id"]

        dashboard = client.get(f"/api/v1/users/{user_id}/dashboard")
        dashboard.raise_for_status()
        dashboard_payload = dashboard.json()

        report = client.get(f"/api/v1/users/{user_id}/doctor-report")
        report.raise_for_status()
        report_payload = report.json()

    print(f"LifeTwin AI demo user: {user_id}")
    print(f"Dashboard: {BASE_URL}/api/v1/users/{user_id}/dashboard")
    print(f"Doctor report: {BASE_URL}/api/v1/users/{user_id}/doctor-report")
    print("\nTop risk factors:")
    for factor in dashboard_payload.get("top_risk_factors", [])[:5]:
        print(f"- [{factor['severity']}] {factor['factor']}: {factor['suggested_action']}")

    print("\nToday actions:")
    for action in dashboard_payload.get("today_actions", [])[:5]:
        print(f"- [{action['priority']}] {action['recommended_action']}")

    print("\nDoctor report summary:")
    latest_risk = report_payload.get("latest_risk_scores") or {}
    print(f"- Overall risk level: {latest_risk.get('overall_risk_level', 'not calculated')}")
    print(f"- Alerts: {len(report_payload.get('recent_alerts', []))}")


if __name__ == "__main__":
    main()
