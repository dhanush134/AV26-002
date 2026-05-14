from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import PreventiveAlert
from app.repositories import health_repository, risk_repository, user_repository, wearable_repository


def _alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    recommended_action: str,
    source: str,
) -> dict:
    return {
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "recommended_action": recommended_action,
        "source": source,
    }


def generate_alert_payloads(db: Session, user_id: UUID) -> list[dict]:
    latest = wearable_repository.get_latest_reading(db, user_id)
    recent = wearable_repository.get_recent_readings(db, user_id, limit=7)
    latest_lab = health_repository.get_latest_lab_report(db, user_id)
    latest_risk = risk_repository.get_latest_risk_score(db, user_id)
    alerts: list[dict] = []

    if latest and latest.resting_heart_rate and latest.resting_heart_rate > 90:
        alerts.append(
            _alert(
                "cardio_pattern",
                "warning",
                "Elevated resting HR pattern",
                "Recent resting heart rate is above the preferred recovery range.",
                "Hydrate, prioritize sleep, reduce stimulant load, and consult a professional if persistent.",
                "wearable",
            )
        )
    cardiac_strain_points = sum(
        1
        for reading in recent
        if reading.heart_rate is not None
        and reading.heart_rate >= 110
        and (reading.active_minutes or 0) <= 5
    )
    if cardiac_strain_points >= 3:
        alerts.append(
            _alert(
                "cardiac_strain_pattern",
                "critical",
                "Repeated high HR while inactive",
                "Several recent readings show elevated heart rate with little or no recorded activity.",
                "Pause intense activity, recheck readings, and consult a qualified healthcare professional if repeated or symptomatic.",
                "wearable",
            )
        )
    if latest and latest.spo2 and latest.spo2 < 94:
        alerts.append(
            _alert(
                "respiratory_pattern",
                "critical" if latest.spo2 < 90 else "warning",
                "Lower SpO2 wellness signal",
                "Recent SpO2 is below the preferred preventive wellness range.",
                "Recheck with a reliable device and consult a qualified healthcare professional if repeated.",
                "wearable",
            )
        )
    poor_sleep_days = sum(1 for reading in recent if reading.sleep_hours is not None and reading.sleep_hours < 6)
    if poor_sleep_days >= 3:
        alerts.append(
            _alert(
                "sleep_recovery",
                "warning",
                "Repeated short sleep pattern",
                "Multiple recent readings show sleep below 6 hours.",
                "Move bedtime earlier and protect a consistent 7-8 hour sleep opportunity.",
                "wearable",
            )
        )
    low_activity_days = sum(1 for reading in recent if reading.steps is not None and reading.steps < 4000)
    if low_activity_days >= 3:
        alerts.append(
            _alert(
                "activity_trend",
                "info",
                "Low activity trend",
                "Recent step counts suggest a low activity trajectory.",
                "Start with two 10-minute walks and progress toward 8000 steps.",
                "wearable",
            )
        )
    if latest_lab and (
        (latest_lab.bp_systolic is not None and latest_lab.bp_systolic >= 130)
        or (latest_lab.bp_diastolic is not None and latest_lab.bp_diastolic >= 80)
        or (latest_lab.ldl is not None and latest_lab.ldl >= 130)
    ):
        alerts.append(
            _alert(
                "cardiometabolic_marker",
                "warning",
                "Cardiometabolic marker attention",
                "Latest lab values show possible elevated preventive cardio risk patterns.",
                "Track BP, reduce fried foods, improve fiber intake, and review labs with a clinician.",
                "lab_report",
            )
        )
    if latest_risk and latest_risk.metabolic_score >= 60:
        alerts.append(
            _alert(
                "metabolic_pattern",
                "warning",
                "Metabolic risk pattern",
                "Combined profile and lab signals suggest a higher preventive metabolic risk pattern.",
                "Prioritize post-meal walks, sleep consistency, and professional preventive guidance.",
                "risk_engine",
            )
        )
    return alerts


def generate_and_store_alerts(db: Session, user_id: UUID) -> list[PreventiveAlert]:
    user_repository.ensure_user(db, user_id)
    created: list[PreventiveAlert] = []
    for payload in generate_alert_payloads(db, user_id):
        exists = db.scalar(
            select(PreventiveAlert)
            .where(
                PreventiveAlert.user_id == user_id,
                PreventiveAlert.alert_type == payload["alert_type"],
                PreventiveAlert.acknowledged.is_(False),
            )
            .limit(1)
        )
        if exists:
            continue
        alert = PreventiveAlert(user_id=user_id, **payload)
        db.add(alert)
        created.append(alert)
    db.commit()
    for alert in created:
        db.refresh(alert)
    return created
